from .base import Plugin
import config


class BookPlugin(Plugin):
    def fetch(self, book_id: str) -> dict:
        search_data = self._fetch_search(book_id)
        epub_data = self._fetch_epub(book_id)

        return {
            "id": book_id,
            "ourn": epub_data.get("ourn"),
            "title": epub_data.get("title"),
            "authors": search_data.get("authors", []),
            "publishers": search_data.get("publishers", []),
            "description": epub_data.get("descriptions", {}).get("text/html", ""),
            "cover_url": search_data.get("cover_url"),
            "isbn": epub_data.get("isbn"),
            "language": epub_data.get("language", "en"),
            "publication_date": epub_data.get("publication_date"),
            "virtual_pages": epub_data.get("virtual_pages"),
            "chapters_url": epub_data.get("chapters"),
            "toc_url": epub_data.get("table_of_contents"),
            "spine_url": epub_data.get("spine"),
            "files_url": epub_data.get("files"),
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

    def search(self, query: str, limit: int = 10) -> list[dict]:
        url = f"{config.API_V2}/search/?query={query}&limit={limit}"
        data = self.http.get_json(url)
        results = []
        for item in data.get("results", []):
            if item.get("content_format") != "book":
                continue
            results.append({
                "id": item.get("archive_id"),
                "title": item.get("title"),
                "authors": item.get("authors", []),
                "cover_url": item.get("cover_url"),
                "publishers": item.get("publishers", []),
            })
        return results
