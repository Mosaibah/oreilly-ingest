from .base import Plugin
from core.types import ChapterInfo
import config


class ChaptersPlugin(Plugin):
    """Plugin for fetching book chapters and their content."""

    def fetch_list(self, book_id: str) -> list[ChapterInfo]:
        """Fetch list of chapters for a book."""
        url = f"{config.API_V2}/epub-chapters/?epub_identifier=urn:orm:book:{book_id}"
        chapters: list[ChapterInfo] = []

        while url:
            data = self.http.get_json(url)
            for ch in data.get("results", []):
                chapters.append(
                    ChapterInfo(
                        ourn=ch.get("ourn", ""),
                        title=ch.get("title", ""),
                        filename=self._extract_filename(ch.get("reference_id", "")),
                        content_url=ch.get("content_url", ""),
                        images=ch.get("related_assets", {}).get("images", []),
                        stylesheets=ch.get("related_assets", {}).get("stylesheets", []),
                        virtual_pages=ch.get("virtual_pages"),
                        minutes_required=ch.get("minutes_required"),
                    )
                )
            url = data.get("next")

        return self._reorder_cover_first(chapters)

    def fetch_toc(self, book_id: str) -> list[dict]:
        url = f"{config.API_V2}/epubs/urn:orm:book:{book_id}/table-of-contents/"
        return self.http.get_json(url)

    def fetch_file_list(self, files_url: str) -> dict[str, dict]:
        """Fetch the full EPUB file manifest and return a dict keyed by filename.

        Uses the /api/v2/epubs/{ourn}/files/ endpoint which returns complete,
        untruncated chapter content — unlike the content_url from epub-chapters/.

        Args:
            files_url: Base URL for the EPUB files manifest endpoint.

        Returns:
            A dict mapping each file's basename (e.g. ``ch01.xhtml``) to its
            full manifest entry, which includes the ``url`` field for fetching
            the raw XHTML.
        """
        # First request: discover the total entry count
        first = self.http.get_json(f"{files_url}?limit=1")
        count = first.get("count", 1)

        # Second request: retrieve the complete manifest
        all_files = self.http.get_json(f"{files_url}?limit={count}")

        file_map: dict[str, dict] = {}
        for entry in all_files.get("results", []):
            full_path = entry.get("full_path", "")
            filename = full_path.split("/")[-1]
            file_map[filename] = entry

        return file_map

    def fetch_content(self, content_url: str) -> str:
        return self.http.get_text(content_url)

    def _extract_filename(self, reference_id: str) -> str:
        if "-/" in reference_id:
            return reference_id.split("-/")[1]
        return reference_id

    def _reorder_cover_first(self, chapters: list[ChapterInfo]) -> list[ChapterInfo]:
        """Reorder chapters to ensure cover comes first."""
        cover_chapters: list[ChapterInfo] = []
        other_chapters: list[ChapterInfo] = []

        for ch in chapters:
            filename_lower = ch["filename"].lower()
            title_lower = ch["title"].lower()
            if "cover" in filename_lower or "cover" in title_lower:
                cover_chapters.append(ch)
            else:
                other_chapters.append(ch)

        return cover_chapters + other_chapters
