"""CLI command implementations."""

import signal
import sys
import uuid
import threading
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from core import create_default_kernel
from core.http_client import HttpClient
from core.state import CookieHandler, QueueItem, QueueManager
from plugins.downloader import DownloadProgress
from plugins.chunking import ChunkConfig

from .formatter import CliFormatter, ProgressState


class DownloadCommand:
    """Handle download operations."""

    def __init__(self, cookie_path: Optional[Path] = None):
        """
        Initialize download command.

        Args:
            cookie_path: Path to cookies file.
        """
        http = HttpClient(cookie_path)

        if not http._auth_cookies:
            raise RuntimeError(
                "No cookies found. Please ensure cookies.json or cookies.txt exists in core/state.\n"
                "You can export cookies from your browser using the Netscape Cookie File format.\n"
                "Or visit the web UI to upload cookies."
            )

        # Create kernel with custom HTTP client
        self.kernel = create_default_kernel()
        self.kernel.http = http
        self.progress_state = ProgressState()
        self._cancel_requested = False

    def _handle_sigint(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n")
        CliFormatter.print_warning("Download cancelled by user")
        self._cancel_requested = True
        sys.exit(1)

    def download(
        self,
        book_id: str,
        formats: list[str],
        output_dir: Path,
        all_chapters: bool = True,
        selected_chapters: Optional[list[int]] = None,
        skip_images: bool = False,
        combined: bool = True,
        chunk_size: Optional[int] = None,
        progress_position: int = 0,
        progress_label: str = "Download",
    ) -> bool:
        """
        Download a book.

        Args:
            book_id: O'Reilly book ID.
            formats: List of output formats.
            output_dir: Output directory path.
            all_chapters: Download all chapters.
            selected_chapters: Specific chapters to download.
            skip_images: Skip image downloads.
            combined: Combine into single file (for applicable formats).
            chunk_size: Chunk size for chunking plugin.

        Returns:
            True if successful, False otherwise.
        """
        # Setup signal handler only on the main thread.
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._handle_sigint)

        try:
            # Validate session
            CliFormatter.print_info("Validating session...")
            auth = self.kernel["auth"]
            if not auth.validate_session():
                CliFormatter.print_error("Session invalid. Please update cookies.")
                return False

            CliFormatter.print_complete("Session valid")

            # Create output directory
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create tqdm progress bar
            pbar = tqdm(
                total=100,
                desc=progress_label,
                unit="%",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}%",
                position=progress_position,
            )
            last_percentage = [0]  # Use list to allow mutation in nested function

            def on_progress(progress: DownloadProgress):
                # Update progress bar based on percentage change
                delta = progress.percentage - last_percentage[0]
                if delta > 0:
                    pbar.update(delta)
                    last_percentage[0] = progress.percentage

                # Update description with status and message
                desc_parts = [progress.status.upper()]
                if progress.current_chapter > 0 and progress.total_chapters > 0:
                    desc_parts.append(
                        f"Ch {progress.current_chapter}/{progress.total_chapters}"
                    )
                if progress.chapter_title:
                    desc_parts.append(f"({progress.chapter_title[:20]})")
                if progress.message:
                    desc_parts.append(progress.message)

                pbar.set_description(" | ".join(desc_parts))

            # Setup chunk config if needed
            chunk_config = None
            if chunk_size:
                chunk_config = ChunkConfig(chunk_size=chunk_size)

            # Perform download
            downloader = self.kernel["downloader"]
            result = downloader.download(
                book_id=book_id,
                output_dir=output_dir,
                formats=formats,
                selected_chapters=selected_chapters if not all_chapters else None,
                skip_images=skip_images,
                chunk_config=chunk_config,
                progress_callback=on_progress,
                cancel_check=lambda: self._cancel_requested,
            )

            # Close progress bar
            pbar.close()

            # Print results
            CliFormatter.print_complete(f"Download complete: {result.title}")
            CliFormatter.print_info(f"Output directory: {result.output_dir}")

            if result.files:
                CliFormatter.print_info(f"Generated formats:")
                for fmt, path in result.files.items():
                    if isinstance(path, list):
                        CliFormatter.print_info(f"  - {fmt}: {len(path)} file(s)")
                    else:
                        path_obj = Path(path)
                        CliFormatter.print_info(f"  - {fmt}: {path_obj.name}")

            return True

        except Exception as e:
            CliFormatter.print_error(f"Download failed: {str(e)}")
            return False

    def validate_auth(self) -> bool:
        """Validate authentication."""
        try:
            auth = self.kernel["auth"]
            return auth.validate_session()
        except Exception:
            return False


class QueueCommand:
    """Handle queue operations."""

    def __init__(self):
        """Initialize queue command."""
        self.queue_manager = QueueManager()

    def add_download(
        self,
        book_id: str,
        formats: list[str],
        output_dir: Path,
        all_chapters: bool = True,
        selected_chapters: Optional[list[int]] = None,
        skip_images: bool = False,
        combined: bool = True,
        chunk_size: Optional[int] = None,
    ) -> str:
        """
        Add download task to queue.

        Returns:
            Task ID.
        """
        item = QueueItem(
            id=str(uuid.uuid4())[:8],
            book_id=book_id,
            formats=formats,
            output_dir=str(output_dir),
            all_chapters=all_chapters,
            selected_chapters=selected_chapters,
            skip_images=skip_images,
            chunk_size=chunk_size,
        )

        task_id = self.queue_manager.add(item)
        CliFormatter.print_info(f"Added to queue: {book_id} (Task ID: {task_id})")
        return task_id

    def list_queue(self) -> list[dict]:
        """List all queued tasks."""
        items = self.queue_manager.list_all()

        if not items:
            CliFormatter.print_info("Queue is empty")
            return []

        headers = ["ID", "Book ID", "Formats", "Status", "Created"]
        rows = []

        for item in items:
            formats_str = ", ".join(item.formats)
            created = item.created_at.split("T")[0]
            rows.append(
                [
                    item.id,
                    item.book_id,
                    formats_str[:30] + "..." if len(formats_str) > 30 else formats_str,
                    item.status,
                    created,
                ]
            )

        CliFormatter.print_table(headers, rows)
        return [item.to_dict() for item in items]

    def remove_from_queue(self, task_id: str) -> bool:
        """Remove task from queue."""
        if self.queue_manager.remove(task_id):
            CliFormatter.print_complete(f"Removed task: {task_id}")
            return True
        else:
            CliFormatter.print_error(f"Task not found: {task_id}")
            return False

    def process_queue(self, cookie_path: Optional[Path] = None):
        """Process all pending tasks in queue."""
        pending = self.queue_manager.list_pending()

        if not pending:
            CliFormatter.print_info("No pending tasks in queue")
            return

        print()
        CliFormatter.print_info(f"Processing {len(pending)} pending tasks...")
        print()

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def run_download(
            item: QueueItem, position: int
        ) -> tuple[str, bool, str | None]:
            downloader = DownloadCommand(cookie_path)
            success = downloader.download(
                book_id=item.book_id,
                formats=item.formats,
                output_dir=Path(item.output_dir),
                all_chapters=item.all_chapters,
                selected_chapters=item.selected_chapters,
                skip_images=item.skip_images,
                chunk_size=item.chunk_size,
                progress_position=position,
                progress_label=item.book_id,
            )
            return item.id, success, None if success else "Download failed"

        max_workers = min(4, len(pending))

        with tqdm(
            total=len(pending), desc="Queue", unit="task", position=0, leave=True
        ) as queue_pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_item = {}
                for position, item in enumerate(pending, 1):
                    self.queue_manager.update_status(item.id, "processing")
                    future = executor.submit(run_download, item, position)
                    future_to_item[future] = item

                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        item_id, success, error_message = future.result()
                        if success:
                            self.queue_manager.update_status(item_id, "completed")
                        else:
                            self.queue_manager.update_status(
                                item_id, "failed", error_message
                            )
                    except Exception as e:
                        self.queue_manager.update_status(item.id, "failed", str(e))
                        CliFormatter.print_error(f"Task failed: {str(e)}")
                    finally:
                        queue_pbar.update(1)

        # Summary
        all_items = self.queue_manager.list_all()
        completed = len([i for i in all_items if i.status == "completed"])
        failed = len([i for i in all_items if i.status == "failed"])

        print()
        CliFormatter.print_info(f"Queue processing complete:")
        CliFormatter.print_complete(f"  ✓ Completed: {completed}")
        if failed > 0:
            CliFormatter.print_error(f"  ✗ Failed: {failed}")
        print()


class ConfigCommand:
    """Handle configuration checks and display."""

    def check_config(self, cookie_path: Optional[Path] = None) -> bool:
        """
        Check and display configuration.

        Args:
            cookie_path: Path to cookies file.

        Returns:
            True if all checks pass, False otherwise.
        """
        import config

        all_good = True

        # Section 1: Configuration Paths
        print()
        CliFormatter.print_info("=" * 50)
        CliFormatter.print_info("Configuration Check")
        CliFormatter.print_info("=" * 50)
        print()

        CliFormatter.print_info("Paths & Configuration:")
        CliFormatter.print_info(f"  Base URL: {config.BASE_URL}")
        CliFormatter.print_info(f"  API V1: {config.API_V1}")
        CliFormatter.print_info(f"  API V2: {config.API_V2}")
        CliFormatter.print_info(f"  Output Directory: {config.OUTPUT_DIR}")
        CliFormatter.print_info(f"  Cookies File: {config.COOKIES_FILE}")
        print()

        # Section 2: Check Cookies
        CliFormatter.print_info("Cookies:")
        cookies = CookieHandler.load_cookies(cookie_path)
        if cookies:
            CliFormatter.print_complete(f"  ✓ Cookies found ({len(cookies)} cookie(s))")
            print()
        else:
            CliFormatter.print_error("  ✗ No cookies found")
            CliFormatter.print_info(
                "    Place cookies.json or cookies.txt in core/state"
            )
            all_good = False
            print()

        # Section 3: Check Authentication (if cookies exist)
        if cookies:
            CliFormatter.print_info("Authentication:")
            try:
                http = HttpClient()
                http._auth_cookies = cookies
                http._apply_auth_cookies()

                kernel = create_default_kernel()
                kernel.http = http

                auth = kernel["auth"]
                status = auth.get_status()

                if status.get("valid"):
                    CliFormatter.print_complete(f"  ✓ Session valid")
                    if status.get("user_type"):
                        CliFormatter.print_info(
                            f"    User Type: {status.get('user_type')}"
                        )
                else:
                    CliFormatter.print_error(
                        f"  ✗ Session invalid ({status.get('reason', 'unknown')})"
                    )
                    all_good = False

            except Exception as e:
                CliFormatter.print_error(f"  ✗ Failed to validate: {str(e)}")
                all_good = False

            print()

        # Section 4: Check Output Directory
        CliFormatter.print_info("Output Directory:")
        if config.OUTPUT_DIR.exists():
            CliFormatter.print_complete(f"  ✓ Exists and is writable")
        else:
            try:
                config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                CliFormatter.print_complete(f"  ✓ Created")
            except Exception as e:
                CliFormatter.print_error(f"  ✗ Cannot create: {str(e)}")
                all_good = False

        print()

        # Final Summary
        if all_good:
            CliFormatter.print_complete("✓ All checks passed!")
        else:
            CliFormatter.print_warning("⚠ Some checks failed. See above for details.")

        print()
        return all_good
