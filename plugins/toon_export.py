"""TOON export plugin for token-efficient LLM pipeline integration."""

from pathlib import Path

from toon_format import encode
from utils.files import sanitize_filename

from .json_export import JsonExportPlugin


class ToonExportPlugin(JsonExportPlugin):
    """Generate TOON (Token-Oriented Object Notation) output for AI/LLM workflows.

    TOON is a lossless, token-efficient encoding of the JSON data model
    (https://toonformat.dev). Reuses the JSON export structure and swaps
    the serializer, so .toon output decodes to the same data as the
    .json export.
    """

    def generate(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
    ) -> Path:
        """Generate TOON export (.toon)."""
        export_data = self._build_export_structure(book_metadata, chapters_data)

        title = book_metadata.get("title", "Unknown")
        safe_title = sanitize_filename(title)

        toon_path = book_dir / f"{safe_title}.toon"
        with open(toon_path, "w", encoding="utf-8") as f:
            f.write(encode(export_data))

        return toon_path
