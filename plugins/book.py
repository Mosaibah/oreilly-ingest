import re

from .base import Plugin
import config


_COVER_WIDTH_RE = re.compile(r'/\d+w/?$')
_HIGH_RES_COVER_WIDTH = '1200w'


def _upgrade_cover_url(url: str) -> str:
    """Upgrade an O'Reilly cover URL to a high-resolution variant.

    O'Reilly serves covers at /library/cover/{isbn}/ and /covers/urn:orm:book:{id}/,
    optionally with a /{N}w/ width segment. The base URL (no width) returns a
    low-res thumbnail (~160x184). Appending /1200w/ returns a print-quality image.
    """
    if "/library/cover/" not in url and "/covers/urn:orm:book:" not in url:
        return url
    # Strip any existing width segment from the end, then append high-res width.
    stripped = _COVER_WIDTH_RE.sub("", url, count=1).rstrip("/")
    return f"{stripped}/{_HIGH_RES_COVER_WIDTH}/"


class BookPlugin(Plugin):
    SUPPORTED_CONTENT_FORMATS = ("book", "video")

    def fetch(self, book_id: str) -> dict:
        search_data = self._fetch_search(book_id)
        content_format = search_data.get("content_format", "book")

        if content_format == "video":
            return self._fetch_video_course(book_id, search_data)

        try:
            epub_data = self._fetch_epub(book_id)
        except Exception:
            # Fallback to video playlist if book_id is actually a video course
            return self._fetch_video_course(book_id, search_data)

        cover_url = search_data.get("cover_url")
        if cover_url:
            cover_url = _upgrade_cover_url(cover_url)

        return {
            "id": book_id,
            "ourn": epub_data.get("ourn", ""),
            "content_format": "book",
            "title": epub_data.get("title") or search_data.get("title") or "Unknown",
            "authors": search_data.get("authors", []),
            "publishers": search_data.get("publishers", []),
            "description": (epub_data.get("descriptions") or {}).get("text/html", "")
            or search_data.get("description", ""),
            "cover_url": cover_url,
            "isbn": epub_data.get("isbn", ""),
            "language": epub_data.get("language", "en"),
            "publication_date": epub_data.get("publication_date", ""),
            "virtual_pages": epub_data.get("virtual_pages"),
            "duration_seconds": None,
            "resources": [],
            "quizzes": [],
            "chapters_url": epub_data.get("chapters"),
            "toc_url": epub_data.get("table_of_contents"),
            "spine_url": epub_data.get("spine"),
            "files_url": epub_data.get("files"),
        }

    def _fetch_video_course(self, book_id: str, search_data: dict) -> dict:
        playlist = self._fetch_video_playlist(book_id)
        ourn = playlist.get("ourn") or search_data.get("ourn") or f"urn:orm:video:{book_id}"

        cover_url = search_data.get("cover_url")
        if not cover_url and playlist.get("cover"):
            cover_path = playlist["cover"]
            cover_url = (
                cover_path
                if cover_path.startswith("http")
                else f"{config.BASE_URL}{cover_path}"
            )
        if cover_url:
            cover_url = _upgrade_cover_url(cover_url)

        contributors = playlist.get("contributors") or {}
        authors = (
            search_data.get("authors")
            or contributors.get("authors")
            or contributors.get("presenters")
            or []
        )
        publishers = search_data.get("publishers") or []
        if not publishers and isinstance(playlist.get("publisher"), dict):
            pub_name = playlist["publisher"].get("name")
            if pub_name:
                publishers = [pub_name]

        raw_duration = playlist.get("total_running_time_secs") or search_data.get("duration_seconds")
        try:
            duration_seconds = int(float(raw_duration)) if raw_duration is not None else None
        except (ValueError, TypeError):
            duration_seconds = None

        quizzes = self._fetch_video_quizzes(ourn)

        return {
            "id": book_id,
            "ourn": ourn,
            "content_format": "video",
            "title": playlist.get("title") or search_data.get("title") or "Unknown",
            "authors": authors,
            "publishers": publishers,
            "description": (playlist.get("descriptions") or {}).get("text/html", "")
            or search_data.get("description", ""),
            "cover_url": cover_url,
            "isbn": playlist.get("isbn") or book_id,
            "language": playlist.get("language") or search_data.get("language", "en"),
            "publication_date": playlist.get("publication_date") or (search_data.get("issued") or "")[:10],
            "virtual_pages": None,
            "duration_seconds": duration_seconds,
            "resources": playlist.get("resources") or [],
            "quizzes": quizzes,
            "chapters_url": f"{config.API_V1}/videoplaylists/{book_id}/",
            "toc_url": playlist.get("toc_url") or f"{config.API_V1}/videotocs/{book_id}/",
            "spine_url": None,
            "files_url": None,
        }

    def _fetch_search(self, book_id: str) -> dict:
        url = f"{config.API_V2}/search/?query={book_id}&limit=1"
        data = self.http.get_json(url)
        results = data.get("results", [])
        if not results:
            return {}
        return results[0]

    def _fetch_epub(self, book_id: str) -> dict:
        url = f"{config.API_V2}/epubs/urn:orm:book:{book_id}/"
        return self.http.get_json(url)

    def _fetch_video_playlist(self, book_id: str) -> dict:
        url = f"{config.API_V1}/videoplaylists/{book_id}/"
        return self.http.get_json(url)

    def _fetch_video_quizzes(self, ourn: str) -> list[dict]:
        try:
            url = f"{config.API_V1}/quiz/by-work/{ourn}/"
            resp = self.http.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", []) if isinstance(data, dict) else []
        except Exception:
            pass
        return []

    def _extract_year(self, item: dict) -> int | None:
        raw = item.get("issued") or item.get("publication_date") or item.get("date_added")
        if raw:
            m = re.search(r"\b(19\d{2}|20\d{2})\b", str(raw))
            if m:
                return int(m.group(1))
        return None

    def search(self, query: str, limit: int = 25) -> list[dict]:
        url = f"{config.API_V2}/search/?query={query}&limit={limit}"
        data = self.http.get_json(url)
        results = []
        for item in data.get("results", []):
            fmt = item.get("content_format")
            if fmt not in self.SUPPORTED_CONTENT_FORMATS:
                continue
            results.append({
                "id": item.get("archive_id"),
                "title": item.get("title"),
                "authors": item.get("authors", []),
                "cover_url": item.get("cover_url"),
                "publishers": item.get("publishers", []),
                "content_format": fmt,
                "duration_seconds": item.get("duration_seconds"),
                "issued": item.get("issued"),
                "publication_year": self._extract_year(item),
            })
        return results
