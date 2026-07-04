"""Main CLI entry point and argument parser."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .commands import DownloadCommand, QueueCommand, ConfigCommand
from .formatter import CliFormatter
from plugins.downloader import DownloaderPlugin


class CLIApp:
    """Main CLI application."""

    def __init__(self, epilog: str = ""):
        """Initialize CLI app."""
        self.epilog = epilog
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser."""
        parser = argparse.ArgumentParser(
            description="O'Reilly Book Downloader - CLI Interface",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Download command
        download_parser = subparsers.add_parser(
            "download",
            help="Download a book",
            description="Download an O'Reilly book in specified formats",
        )
        self._add_download_args(download_parser)

        # Queue commands
        queue_parser = subparsers.add_parser(
            "queue",
            help="Manage download queue",
        )
        queue_subparsers = queue_parser.add_subparsers(
            dest="queue_command", help="Queue operations"
        )

        # queue add
        queue_add_parser = queue_subparsers.add_parser("add", help="Add to queue")
        self._add_download_args(queue_add_parser)

        # queue list
        queue_subparsers.add_parser("list", help="List queued items")

        # queue remove
        queue_remove_parser = queue_subparsers.add_parser(
            "remove", help="Remove from queue"
        )
        queue_remove_parser.add_argument("task_id", help="Task ID to remove")

        # queue process
        queue_process_parser = queue_subparsers.add_parser(
            "process",
            help="Process all pending tasks",
        )
        queue_process_parser.add_argument(
            "--cookies",
            type=Path,
            help="Path to cookies file (JSON or Netscape format)",
        )

        # Config command
        config_parser = subparsers.add_parser(
            "config",
            help="Check configuration and status",
            description="Display configuration, paths, and validate setup",
        )
        config_parser.add_argument(
            "--cookies",
            type=Path,
            help="Path to cookies file (JSON or Netscape format)",
        )

        return parser

    def _add_download_args(self, parser: argparse.ArgumentParser):
        """Add download arguments to a parser."""
        parser.add_argument(
            "book_id",
            help="O'Reilly book ID (e.g., 0123456789 or urn:orm:book:xxxxx)",
        )

        parser.add_argument(
            "--format",
            "-f",
            default="epub",
            help="Output format(s): epub, markdown, json, plaintext, pdf, chunks. "
            "Use comma for multiple: 'markdown,pdf,json'. Default: epub",
        )

        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            default=Path("output"),
            help="Output directory. Default: output/",
        )

        parser.add_argument(
            "--chapters",
            "-c",
            choices=["all", "selected"],
            default="all",
            help="Chapter selection mode. Default: all",
        )

        parser.add_argument(
            "--chapter-list",
            type=str,
            help="Comma-separated list of chapter numbers to download "
            "(only with --chapters selected). Example: 1,2,3,5",
        )

        parser.add_argument(
            "--combined",
            action="store_true",
            default=True,
            help="Combine into single file (for markdown, json, plaintext, pdf). Default: True",
        )

        parser.add_argument(
            "--separate",
            dest="combined",
            action="store_false",
            help="Generate separate files per chapter (for markdown, json, plaintext, pdf)",
        )

        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip downloading images",
        )

        parser.add_argument(
            "--chunk-size",
            type=int,
            help="Chunk size for chunking plugin (tokens). Default: 4000",
        )

        parser.add_argument(
            "--cookies",
            type=Path,
            help="Path to cookies file (JSON or Netscape format)",
        )

    def run(self, args: Optional[list[str]] = None) -> int:
        """
        Run the CLI.

        Args:
            args: Command line arguments. If None, uses sys.argv[1:].

        Returns:
            Exit code.
        """
        if args is None:
            args = sys.argv[1:]

        # Show help if no arguments
        if not args:
            self.parser.print_help()
            return 0

        parsed_args = self.parser.parse_args(args)

        try:
            if parsed_args.command == "download":
                return self._handle_download(parsed_args)
            elif parsed_args.command == "queue":
                return self._handle_queue(parsed_args)
            elif parsed_args.command == "config":
                return self._handle_config(parsed_args)
            else:
                self.parser.print_help()
                return 1

        except KeyboardInterrupt:
            CliFormatter.print_warning("Interrupted by user")
            return 130
        except Exception as e:
            CliFormatter.print_error(f"Error: {str(e)}")
            return 1

    def _handle_download(self, args) -> int:
        """Handle download command."""
        try:
            # Parse formats
            formats = DownloaderPlugin.parse_formats(args.format)

            # Validate chapter selection
            selected_chapters = None
            if args.chapters == "selected":
                if not args.chapter_list:
                    CliFormatter.print_error(
                        "--chapter-list required with --chapters selected"
                    )
                    return 1

                try:
                    selected_chapters = [
                        int(ch.strip()) for ch in args.chapter_list.split(",")
                    ]
                except ValueError:
                    CliFormatter.print_error(
                        "Invalid chapter list format. Use comma-separated numbers: 1,2,3"
                    )
                    return 1

            # Perform download
            downloader = DownloadCommand(args.cookies)

            success = downloader.download(
                book_id=args.book_id,
                formats=formats,
                output_dir=args.output,
                all_chapters=(args.chapters == "all"),
                selected_chapters=selected_chapters,
                skip_images=args.skip_images,
                combined=args.combined,
                chunk_size=args.chunk_size,
            )

            return 0 if success else 1

        except RuntimeError as e:
            CliFormatter.print_error(str(e))
            return 1

    def _handle_queue(self, args) -> int:
        """Handle queue command."""
        queue_cmd = QueueCommand()

        if args.queue_command == "add":
            try:
                # Parse formats
                formats = DownloaderPlugin.parse_formats(args.format)

                # Validate chapter selection
                selected_chapters = None
                if args.chapters == "selected":
                    if not args.chapter_list:
                        CliFormatter.print_error(
                            "--chapter-list required with --chapters selected"
                        )
                        return 1

                    try:
                        selected_chapters = [
                            int(ch.strip()) for ch in args.chapter_list.split(",")
                        ]
                    except ValueError:
                        CliFormatter.print_error(
                            "Invalid chapter list format. Use comma-separated numbers: 1,2,3"
                        )
                        return 1

                # Add to queue
                queue_cmd.add_download(
                    book_id=args.book_id,
                    formats=formats,
                    output_dir=args.output,
                    all_chapters=(args.chapters == "all"),
                    selected_chapters=selected_chapters,
                    skip_images=args.skip_images,
                    combined=args.combined,
                    chunk_size=args.chunk_size,
                )

                return 0

            except RuntimeError as e:
                CliFormatter.print_error(str(e))
                return 1

        elif args.queue_command == "list":
            queue_cmd.list_queue()
            return 0

        elif args.queue_command == "remove":
            success = queue_cmd.remove_from_queue(args.task_id)
            return 0 if success else 1

        elif args.queue_command == "process":
            queue_cmd.process_queue(args.cookies)
            return 0

        else:
            CliFormatter.print_error(
                "Please specify a queue operation: add, list, remove, process"
            )
            return 1

    def _handle_config(self, args) -> int:
        """Handle config command."""
        try:
            config_cmd = ConfigCommand()
            success = config_cmd.check_config(args.cookies)
            return 0 if success else 1
        except Exception as e:
            CliFormatter.print_error(str(e))
            return 1


def main():
    """Main entry point."""
    app = CLIApp()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
