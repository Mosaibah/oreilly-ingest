"""Plain text export plugin for LLM-friendly output."""

from pathlib import Path

from core.text_extractor import TextExtractor
from utils.files import sanitize_filename

from .base import Plugin


class PlainTextPlugin(Plugin):
    """Generate plain text output from processed chapters."""

    def __init__(self):
        self._extractor = TextExtractor()

    def generate(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
        single_file: bool = True,
    ) -> Path:
        """Generate plain text export (single file or per-chapter)."""
        if single_file:
            return self._generate_single_file(book_dir, book_metadata, chapters_data)
        else:
            return self._generate_chapter_files(book_dir, book_metadata, chapters_data)

    def _generate_single_file(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
    ) -> Path:
        """Generate single concatenated text file."""
        title = book_metadata.get("title", "Unknown")
        safe_title = sanitize_filename(title)
        output_path = book_dir / f"{safe_title}.txt"

        content_parts = [self._format_metadata_header(book_metadata)]

        for i, (filename, chapter_title, html) in enumerate(chapters_data, 1):
            text = self._extractor.extract_text_only(html)
            content_parts.append(self._format_chapter(i, chapter_title, text))

        output_path.write_text("\n\n".join(content_parts), encoding="utf-8")
        return output_path

    def _generate_chapter_files(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
    ) -> Path:
        """Generate individual chapter files in PlainText/ subdirectory."""
        txt_dir = book_dir / "PlainText"
        txt_dir.mkdir(parents=True, exist_ok=True)

        readme_parts = [self._format_metadata_header(book_metadata)]
        readme_parts.append("## Chapters\n")

        for i, (filename, chapter_title, html) in enumerate(chapters_data, 1):
            text = self._extractor.extract_text_only(html)
            content = self._format_chapter(i, chapter_title, text)

            txt_filename = self._make_chapter_filename(filename, i)
            (txt_dir / txt_filename).write_text(content, encoding="utf-8")

            readme_parts.append(f"- [{chapter_title}]({txt_filename})")

        (txt_dir / "README.txt").write_text("\n".join(readme_parts), encoding="utf-8")
        return txt_dir

    def _format_metadata_header(self, metadata: dict) -> str:
        """Create metadata header with title, authors, ISBN, publisher."""
        lines = []
        if title := metadata.get("title"):
            lines.append(f"Title: {title}")
        if authors := metadata.get("authors"):
            lines.append(f"Authors: {', '.join(authors)}")
        if isbn := metadata.get("isbn"):
            lines.append(f"ISBN: {isbn}")
        if publishers := metadata.get("publishers"):
            lines.append(f"Publisher: {', '.join(publishers)}")

        if lines:
            lines.append("\n---")
        return "\n".join(lines)

    def _format_chapter(self, index: int, title: str, content: str) -> str:
        """Format a chapter with numbered header."""
        header = f"## Chapter {index}: {title}"
        return f"{header}\n\n{content}"

    def _make_chapter_filename(self, original: str, index: int) -> str:
        """Create chapter filename with order prefix."""
        base = Path(original).stem
        return f"{index:03d}_{base}.txt"
