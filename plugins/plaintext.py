"""
Plain text export plugin for LLM-friendly output.
Strips HTML, preserves code blocks with markdown fences.
"""

from pathlib import Path

from core.text_extractor import TextExtractor

from .base import Plugin


class PlainTextPlugin(Plugin):
    """
    Generate plain text output from processed chapters.

    Output options:
    - Single file: All chapters concatenated with headers
    - Chapter files: Individual .txt files in PlainText/ directory

    Usage:
        plugin = kernel["plaintext"]
        path = plugin.generate(
            book_dir=Path("output/MyBook"),
            book_metadata={"title": "...", "authors": [...]},
            chapters_data=[("ch01.xhtml", "Intro", "<div>...</div>"), ...],
            single_file=True
        )
    """

    def __init__(self):
        self._extractor = TextExtractor()

    def generate(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
        single_file: bool = True,
    ) -> Path:
        """
        Generate plain text export.

        Args:
            book_dir: Output directory for the book
            book_metadata: Dict with title, authors, isbn, etc.
            chapters_data: List of (filename, title, html_content) tuples
            single_file: If True, output single .txt; if False, one file per chapter

        Returns:
            Path to generated file or directory
        """
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
        safe_title = self._sanitize_filename(title)
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
        """
        Create minimal metadata header.

        Format:
            Title: Book Title
            Authors: Author One, Author Two
            ISBN: 978-...

            ---
        """
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
        """
        Format a chapter for text output.

        Format:
            ## Chapter 1: Introduction

            [content]
        """
        header = f"## Chapter {index}: {title}"
        return f"{header}\n\n{content}"

    def _make_chapter_filename(self, original: str, index: int) -> str:
        """Create chapter filename with order prefix."""
        base = Path(original).stem
        return f"{index:03d}_{base}.txt"

    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "")
        return name.strip()[:200]
