"""Output directory management plugin."""

from pathlib import Path

import config
from plugins.base import Plugin
from utils import slugify


class OutputPlugin(Plugin):
    """
    Manages output directories and file organization.

    Responsibilities:
    - Get/validate output directories
    - Create book directories with conflict resolution
    - Handle naming conventions
    """

    def get_default_dir(self) -> Path:
        """Return the default output directory from config."""
        return config.OUTPUT_DIR

    def validate_dir(self, path: str | Path | None) -> tuple[bool, str, Path | None]:
        """
        Validate that a directory exists and is writable.

        Args:
            path: Directory path to validate (None uses default)

        Returns:
            Tuple of (success, message, resolved_path)
        """
        if path is None:
            return True, "Using default directory", self.get_default_dir()

        path = Path(path) if isinstance(path, str) else path

        # Try to create if doesn't exist
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create directory: {e}", None

        if not path.is_dir():
            return False, "Path is not a directory", None

        # Check writability
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            return False, "Directory is not writable", None

        return True, "Directory is valid", path

    def create_book_dir(
        self,
        output_dir: Path,
        book_id: str,
        title: str,
        authors: list[str] | None = None,
    ) -> Path:
        """
        Create a book output directory.

        Args:
            output_dir: Parent output directory
            book_id: Book identifier (for conflict detection)
            title: Book title (used for folder name)
            authors: Optional author list (fallback if no title)

        Returns:
            Path to the created book directory
        """
        # Build folder name with fallback chain
        folder_title = (title or "").strip()
        if not folder_title and authors:
            folder_title = f"Book by {authors[0]}"
        if not folder_title:
            folder_title = book_id

        folder_name = slugify(folder_title)
        book_dir = output_dir / folder_name

        # Handle same-title-different-book conflicts
        book_dir = self._resolve_conflict(book_dir, book_id)

        # Create the directory structure
        oebps = book_dir / "OEBPS"
        oebps.mkdir(parents=True, exist_ok=True)

        # Write book_id for future reference
        meta_file = book_dir / ".book_id"
        meta_file.write_text(book_id)

        return book_dir

    def _resolve_conflict(self, book_dir: Path, book_id: str) -> Path:
        """
        Handle directory conflicts for books with same title but different IDs.

        Args:
            book_dir: Proposed book directory path
            book_id: Current book's ID

        Returns:
            Resolved directory path (may be different if conflict detected)
        """
        meta_file = book_dir / ".book_id"

        if book_dir.exists() and meta_file.exists():
            existing_id = meta_file.read_text().strip()
            if existing_id != book_id:
                # Different book with same title - append book_id
                new_name = f"{book_dir.name}-{book_id}"
                return book_dir.parent / new_name

        return book_dir

    def get_oebps_dir(self, book_dir: Path) -> Path:
        """Get the OEBPS directory for a book."""
        return book_dir / "OEBPS"

    def get_images_dir(self, book_dir: Path) -> Path:
        """Get the Images directory for a book."""
        return book_dir / "OEBPS" / "Images"

    def get_styles_dir(self, book_dir: Path) -> Path:
        """Get the Styles directory for a book."""
        return book_dir / "OEBPS" / "Styles"
