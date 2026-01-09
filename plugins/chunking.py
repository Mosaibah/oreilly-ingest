"""Text chunking plugin for RAG applications."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from core.text_extractor import TextExtractor
from utils.files import sanitize_filename

from .base import Plugin


@dataclass
class ChunkConfig:
    """Configuration for text chunking."""

    chunk_size: int = 4000
    overlap: int = 200
    respect_boundaries: bool = True


class ChunkingPlugin(Plugin):
    """Generate chunked JSONL output for RAG/retrieval applications."""

    SENTENCE_ENDINGS = re.compile(r"[.!?]\s+")
    PARAGRAPH_BREAK = re.compile(r"\n\n+")

    def __init__(self):
        self._extractor = TextExtractor()

    def generate(
        self,
        book_dir: Path,
        book_metadata: dict,
        chapters_data: list[tuple[str, str, str]],
        config: ChunkConfig | None = None,
    ) -> Path:
        """Generate chunked JSONL export."""
        if config is None:
            config = ChunkConfig()

        chunks = self.chunk_book(chapters_data, config)

        title = book_metadata.get("title", "Unknown")
        safe_title = sanitize_filename(title)

        output_path = book_dir / f"{safe_title}_chunks.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        return output_path

    def chunk_book(
        self,
        chapters_data: list[tuple[str, str, str]],
        config: ChunkConfig,
    ) -> list[dict]:
        """Chunk an entire book, preserving chapter metadata."""
        all_chunks = []
        chunk_id = 0

        for chapter_index, (filename, title, html) in enumerate(chapters_data):
            text = self._extractor.extract_text_only(html)

            chapter_chunks = self.chunk_text(
                text,
                config.chunk_size,
                config.overlap,
                config.respect_boundaries,
            )

            for chunk in chapter_chunks:
                chunk["chunk_id"] = chunk_id
                chunk["chapter_index"] = chapter_index
                chunk["chapter_title"] = title
                chunk["chapter_filename"] = filename
                all_chunks.append(chunk)
                chunk_id += 1

        return all_chunks

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200,
        respect_boundaries: bool = True,
    ) -> list[dict]:
        """Chunk text into fixed-size pieces with optional overlap."""
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            target_end = self._estimate_char_position(text, start, chunk_size)
            target_end = min(target_end, text_len)

            if respect_boundaries and target_end < text_len:
                end = self._find_break_point(text, target_end)
            else:
                end = target_end

            if end <= start:
                end = target_end

            chunk_text = text[start:end].strip()
            if chunk_text:
                token_count = self._get_token_count(chunk_text)
                chunks.append(
                    {
                        "content": chunk_text,
                        "token_count": token_count,
                        "start_offset": start,
                        "end_offset": end,
                    }
                )

            overlap_chars = self._estimate_char_position(text, end - overlap * 4, overlap) if overlap > 0 else 0
            next_start = end - min(overlap_chars, end - start - 1)
            start = max(next_start, start + 1)

        return chunks

    def _estimate_char_position(self, text: str, start: int, token_count: int) -> int:
        """Estimate character position for a target token count."""
        estimated_chars = token_count * 4
        target = start + estimated_chars

        if target >= len(text):
            return len(text)

        chunk = text[start:target]
        actual_tokens = self._get_token_count(chunk)

        if actual_tokens < token_count * 0.8:
            ratio = token_count / max(actual_tokens, 1)
            target = start + int(estimated_chars * ratio)
        elif actual_tokens > token_count * 1.2:
            ratio = token_count / actual_tokens
            target = start + int(estimated_chars * ratio)

        return min(target, len(text))

    def _find_break_point(self, text: str, target_pos: int, search_window: int = 500) -> int:
        """Find a paragraph, sentence, or word break near target position."""
        window_start = max(0, target_pos - search_window)
        window_end = min(len(text), target_pos + search_window // 2)
        window = text[window_start:window_end]

        for match in self.PARAGRAPH_BREAK.finditer(window):
            break_pos = window_start + match.end()
            if window_start + search_window // 2 <= break_pos <= window_end:
                return break_pos

        best_sentence_end = None
        for match in self.SENTENCE_ENDINGS.finditer(window):
            break_pos = window_start + match.end()
            if break_pos <= target_pos + search_window // 4:
                best_sentence_end = break_pos

        if best_sentence_end:
            return best_sentence_end

        space_pos = text.rfind(" ", window_start, target_pos + 50)
        if space_pos > window_start:
            return space_pos + 1

        return target_pos

    def _get_token_count(self, text: str) -> int:
        """Get token count via TokenPlugin."""
        try:
            token_plugin = self.kernel.get("token")
            if token_plugin:
                return token_plugin.count_tokens(text)
        except Exception:
            pass
        return int(len(text.split()) * 1.3)
