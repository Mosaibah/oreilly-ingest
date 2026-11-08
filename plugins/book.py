import re
import urllib.parse

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


# ---------------------------------------------------------------------------
# Book-id normalization: URLs, URNs, ISBNs and free-text are all accepted.
#
# The learning.oreilly.com library URLs carry the book's numeric id
# (ISBN-13-like) as the last path segment, e.g.
#   https://learning.oreilly.com/library/view/<slug>/9784814400737/
#   urn:orm:book:9784814400737
# Normalising these to the bare numeric id allows pasting a URL or URN
# directly into the search box (essential for non-English books, whose
# titles cannot be found through the keyword search index).
# ---------------------------------------------------------------------------
_URN_BOOK_RE = re.compile(r"urn:orm:book:([0-9A-Za-z]+?)(?:[:/]|$)")
_LIBRARY_URL_RE = re.compile(r"learning\.oreilly\.com/(?:library/view/)?[^/\s]*/?([0-9]{9,14})(?:[/?#]|\s|$)")
_BARE_ID13_RE = re.compile(r"[0-9]{13}$")
_BARE_ISBN10_RE = re.compile(r"[0-9]{9}[0-9xX]$")


def normalize_book_query(raw: str) -> str | None:
    """Return the bare book id from a URL, URN or bare ISBN-like input.

    Returns None when the text looks like keywords rather than an id.
    """
    text = (raw or "").strip()
    if not text or " " in text.strip():
        # URNs never contain spaces; a lone id never contains spaces either.
        m = _URN_BOOK_RE.search(text)
        return m.group(1) if m else None

    m = _URN_BOOK_RE.search(text)
    if m:
        return m.group(1)

    if "learning.oreilly.com" in text:
        m = _LIBRARY_URL_RE.search(text)
        if m:
            return m.group(1)
        return None

    compact = text.replace("-", "").replace("_", "")
    if _BARE_ID13_RE.match(compact) or _BARE_ISBN10_RE.match(compact):
        return compact
    return None


def looks_like_book_id(book_id: str) -> bool:
    """True when the query is a bare numeric id or ISBN (10 or 13 digits)."""
    if not book_id:
        return False
    return bool(_BARE_ID13_RE.match(book_id) or _BARE_ISBN10_RE.match(book_id))


class BookPlugin(Plugin):
    # ISO codes probed when an ISBN lookup returns nothing without a language
    # filter. The search index cannot match Japanese (and other CJK) metadata
    # against ISBNs unless the matching language filter is supplied, so we
    # probe the most common platform languages until the book is found.
    SEARCH_PROBE_LANGUAGES = ["ja", "zh", "es", "fr", "de", "it", "pt", "ru", "ko"]

    # Languages scanned when looking for translations of a book.
    TRANSLATION_LANGUAGES = ["ja", "zh", "es", "fr", "de", "it", "pt", "ru", "ko"]

    def fetch(self, book_id: str) -> dict:
        epub_data = self._fetch_epub(book_id)
        search_data = self._fetch_search(book_id)

        cover_url = search_data.get("cover_url")
        if cover_url:
            cover_url = _upgrade_cover_url(cover_url)
        else:
            # The search API is the only source for cover URLs, but it needs a
            # fresh (non-expired) session JWT. Cover images themselves are
            # served publicly, so build the absolute URL directly as a
            # fallback (relative paths would break <img> in the web UI).
            cover_url = _upgrade_cover_url(
                f"https://learning.oreilly.com/covers/urn:orm:book:{book_id}/"
            )

        return {
            "id": book_id,
            "ourn": epub_data.get("ourn", ""),
            "title": epub_data.get("title") or "Unknown",
            "authors": search_data.get("authors", []),
            "publishers": search_data.get("publishers", []),
            "description": (epub_data.get("descriptions") or {}).get("text/html", ""),
            "cover_url": cover_url,
            "isbn": epub_data.get("isbn", ""),
            "language": epub_data.get("language", "en"),
            "publication_date": epub_data.get("publication_date", ""),
            "virtual_pages": epub_data.get("virtual_pages"),
            "chapters_url": epub_data.get("chapters"),
            "toc_url": epub_data.get("table_of_contents"),
            "spine_url": epub_data.get("spine"),
            "files_url": epub_data.get("files"),
        }

    def _fetch_search(self, book_id: str) -> dict:
        """Search metadata for one book id.

        Returns {} when the search backend cannot see the book (common for
        non-English editions whose metadata is only indexed under their own
        language) or when the session token is expired — the fallbacks in
        fetch() then cover title/cover/language via the public epub API.
        """
        try:
            url = f"{config.API_V2}/search/?query={urllib.parse.quote(str(book_id))}&limit=1"
            results = self._get_search_results(url)
        except Exception as e:
            print(f"[book] search metadata unavailable for {book_id}: {e}")
            return {}
        if not results and looks_like_book_id(str(book_id)):
            results = self._probe_by_language(str(book_id), limit=1)
        return results[0] if results else {}

    def _fetch_epub(self, book_id: str) -> dict:
        url = f"{config.API_V2}/epubs/urn:orm:book:{book_id}/"
        return self.http.get_json(url)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10, language: str | None = None) -> list[dict]:
        """Keyword search over the platform index.

        `language` (ISO code such as "en" or "ja") is forwarded to the search
        API's `languages` filter so users can browse books in a specific
        language — required to see Japanese/translated editions, which are
        otherwise invisible to keyword queries.
        """
        book_id = normalize_book_query(query) or query.strip()

        params = {"query": book_id, "limit": limit}
        if language:
            params["languages"] = language
        url = f"{config.API_V2}/search/?{urllib.parse.urlencode(params)}"

        results = self._get_search_results(url)

        # ISBN/URL lookups can miss when the book lives in another language's
        # index slice (e.g. Japanese ISBNs are invisible without "languages=ja").
        # Only probe for id-shaped queries: keyword probing would be noise.
        if not results and not language and looks_like_book_id(book_id):
            results = self._probe_by_language(book_id, limit=limit)

        books = []
        seen = set()
        for item in results:
            if item.get("content_format") != "book":
                continue
            book = {
                "id": item.get("archive_id"),
                "title": item.get("title"),
                "authors": item.get("authors", []),
                "cover_url": item.get("cover_url"),
                "publishers": item.get("publishers", []),
                "language": item.get("language", "en"),
                "isbn": item.get("isbn", ""),
            }
            if book["cover_url"]:
                book["cover_url"] = _upgrade_cover_url(book["cover_url"])
            if book["id"] and book["id"] not in seen:
                seen.add(book["id"])
                books.append(book)
        return books

    def _get_search_results(self, url: str) -> list[dict]:
        data = self.http.get_json(url)
        return data.get("results", [])

    def _probe_by_language(self, book_id: str, limit: int) -> list[dict]:
        """Search the same query under each candidate language until it hits.

        Needed because translated editions are only visible when the search
        request carries their language filter.
        """
        for lang in self.SEARCH_PROBE_LANGUAGES:
            params = {"query": book_id, "limit": limit, "languages": lang}
            url = f"{config.API_V2}/search/?{urllib.parse.urlencode(params)}"
            results = self._get_search_results(url)
            if results:
                return results
        return []

    def find_translations(self, book_id: str, limit_per_language: int = 3) -> list[dict]:
        """Find translations of a book in other languages.

        Uses the English (original) title as the search query under each
        language filter, then keeps the best candidates. Translated editions
        carry their own title, so candidates other than the exact match are
        possible — the UI shows the language and cover so the user can verify.
        """
        try:
            epub_data = self._fetch_epub(book_id)
        except Exception as e:
            raise RuntimeError(f"Cannot fetch book {book_id}: {e}") from e

        title = (epub_data.get("title") or "").strip()
        own_language = (epub_data.get("language") or "en")[:2].lower()
        if not title:
            return []

        # The search backend rejects expired tokens; probing every language
        # would just repeat the same 401. Downloads don't need search, so exit
        # quietly instead — the UI treats an empty list as "no editions found".
        jwt_status = self.kernel.http.get_jwt_status()
        if jwt_status is not None and not jwt_status["valid"]:
            print("[book] translations skipped: session token expired (search requires a fresh JWT)")
            return []

        translations = []
        seen = set()
        for lang in self.TRANSLATION_LANGUAGES:
            if lang == own_language:
                continue
            params = {"query": title, "limit": limit_per_language, "languages": lang}
            url = f"{config.API_V2}/search/?{urllib.parse.urlencode(params)}"
            try:
                results = self._get_search_results(url)
            except Exception as e:
                print(f"[book] translation search '{lang}' unavailable: {e}")
                continue
            for item in results:
                if item.get("content_format") != "book":
                    continue
                item_language = (item.get("language") or lang)[:2].lower()
                # Trust only results matching the requested language filter;
                # translation records always carry their own language code.
                if item_language != lang:
                    continue
                item_id = item.get("archive_id")
                if not item_id or item_id in seen:
                    continue
                seen.add(item_id)
                cover_url = item.get("cover_url")
                if cover_url:
                    cover_url = _upgrade_cover_url(cover_url)
                translations.append({
                    "id": item_id,
                    "title": item.get("title"),
                    "authors": item.get("authors", []),
                    "cover_url": cover_url,
                    "publishers": item.get("publishers", []),
                    "language": item_language,
                })
        return translations
