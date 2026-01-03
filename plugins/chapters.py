from .base import Plugin
import config


class ChaptersPlugin(Plugin):
    def fetch_list(self, book_id: str) -> list[dict]:
        url = f"{config.API_V2}/epub-chapters/?epub_identifier=urn:orm:book:{book_id}"
        chapters = []

        while url:
            data = self.http.get_json(url)
            for ch in data.get("results", []):
                chapters.append({
                    "ourn": ch.get("ourn"),
                    "title": ch.get("title"),
                    "filename": self._extract_filename(ch.get("reference_id", "")),
                    "content_url": ch.get("content_url"),
                    "images": ch.get("related_assets", {}).get("images", []),
                    "stylesheets": ch.get("related_assets", {}).get("stylesheets", []),
                    "virtual_pages": ch.get("virtual_pages"),
                    "minutes_required": ch.get("minutes_required"),
                })
            url = data.get("next")

        return self._reorder_cover_first(chapters)

    def fetch_toc(self, book_id: str) -> list[dict]:
        url = f"{config.API_V2}/epubs/urn:orm:book:{book_id}/table-of-contents/"
        return self.http.get_json(url)

    def fetch_content(self, content_url: str) -> str:
        return self.http.get_text(content_url)

    def _extract_filename(self, reference_id: str) -> str:
        if "-/" in reference_id:
            return reference_id.split("-/")[1]
        return reference_id

    def _reorder_cover_first(self, chapters: list[dict]) -> list[dict]:
        cover_chapters = []
        other_chapters = []

        for ch in chapters:
            filename_lower = ch["filename"].lower()
            title_lower = ch["title"].lower()
            if "cover" in filename_lower or "cover" in title_lower:
                cover_chapters.append(ch)
            else:
                other_chapters.append(ch)

        return cover_chapters + other_chapters
