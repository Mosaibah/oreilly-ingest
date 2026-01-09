"""JSON export plugin for RAG/LLM pipeline integration."""

import json
from pathlib import Path

from core.text_extractor import TextExtractor
from utils.files import sanitize_filename

from .base import Plugin


class JsonExportPlugin(Plugin):
    """Generate structured JSON output for AI/LLM workflows."""

    def __init__(self):
        self._extractor = TextExtractor()

    def generate(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
        include_jsonl: bool = False,
    ) -> Path:
        """Generate JSON export (.json and optional .jsonl)."""
        export_data = self._build_export_structure(book_metadata, chapters_data)

        title = book_metadata.get("title", "Unknown")
        safe_title = sanitize_filename(title)

        json_path = book_dir / f"{safe_title}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        if include_jsonl:
            self._write_jsonl(book_dir, safe_title, export_data["chapters"])

        return json_path

    def _build_export_structure(
        self,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
    ) -> dict:
        """Build the complete export data structure."""
        chapters = []
        for i, (filename, title, html) in enumerate(chapters_data):
            chapter_data = self._process_chapter(i, filename, title, html)
            chapters.append(chapter_data)

        return {
            "metadata": {
                "title": book_metadata.get("title", ""),
                "authors": book_metadata.get("authors", []),
                "isbn": book_metadata.get("isbn", ""),
                "publisher": (
                    book_metadata.get("publishers", [""])[0]
                    if book_metadata.get("publishers")
                    else ""
                ),
                "topics": book_metadata.get("topics", []),
            },
            "chapters": chapters,
            "statistics": self._calculate_statistics(chapters),
        }

    def _process_chapter(
        self,
        index: int,
        filename: str,
        title: str,
        html_content: str,
    ) -> dict:
        """Process a single chapter into export structure."""
        extracted = self._extractor.extract(html_content)

        code_blocks = [
            {"language": cb.language, "code": cb.code} for cb in extracted.code_blocks
        ]

        word_count = self._count_words(extracted.text)
        token_count = self._get_token_count(extracted.text)

        return {
            "index": index,
            "title": title,
            "filename": filename,
            "content": extracted.text,
            "code_blocks": code_blocks,
            "word_count": word_count,
            "token_count": token_count,
        }

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())

    def _get_token_count(self, text: str) -> int | None:
        """Get token count via TokenPlugin if available."""
        try:
            token_plugin = self.kernel.get("token")
            if token_plugin:
                return token_plugin.count_tokens(text)
        except Exception:
            pass
        return None

    def _calculate_statistics(self, chapters: list[dict]) -> dict:
        """Calculate aggregate statistics from processed chapters."""
        total_words = sum(ch.get("word_count", 0) for ch in chapters)
        token_counts = [ch.get("token_count") for ch in chapters if ch.get("token_count") is not None]
        total_tokens = sum(token_counts) if token_counts else None

        return {
            "total_chapters": len(chapters),
            "total_words": total_words,
            "total_tokens": total_tokens,
        }

    def _write_jsonl(self, book_dir: Path, title: str, chapters: list[dict]) -> Path:
        """Write chapters as JSONL (one JSON object per line)."""
        jsonl_path = book_dir / f"{title}.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for chapter in chapters:
                f.write(json.dumps(chapter, ensure_ascii=False) + "\n")
        return jsonl_path
