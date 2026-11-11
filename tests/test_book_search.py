"""Unit tests for plugins/book.py query normalization & language probing.

Run from repo root:
    python -m unittest tests/test_book_search.py
    python -m unittest discover tests
"""
import unittest
import urllib.parse
from plugins.book import (
    BookPlugin,
    normalize_book_query,
    looks_like_book_id,
)

JA_ISBN = "9784814400737"
EN_ISBN = "9781098100124"


class StubHttp:
    """Simulates the O'Reilly search backend's language-gated behaviour."""

    def __init__(self):
        self.calls: list[str] = []

    def get_jwt_status(self):
        return {"valid": True, "reason": None}

    def get_json(self, url: str) -> dict:
        self.calls.append(url)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        query = qs["query"][0]
        languages = qs.get("languages", [])

        if query == EN_ISBN and (not languages or any(l in ("en",) for l in languages)):
            return {"results": [self._record(EN_ISBN, "Learning Domain-Driven Design", "en")]}
        if query == JA_ISBN and "ja" in languages:
            return {"results": [self._record(
                JA_ISBN,
                "ドメイン駆動設計をはじめよう ―ソフトウェアの実装と事業戦略を結びつける実践技法",
                "ja",
            )]}
        # Japanese title keywords are unmatchable by the keyword index
        if "ドメイン駆動設計" in query:
            return {"results": []}
        if query == "Learning Domain-Driven Design" and "ja" in languages:
            # Mirrors the live API: the translated edition ranks first
            return {"results": [
                self._record(
                    JA_ISBN,
                    "ドメイン駆動設計をはじめよう ―ソフトウェアの実装と事業戦略を結びつける実践技法",
                    "ja",
                ),
                self._record("9784873119724", "実践 自然言語処理", "ja"),
            ]}
        if query == "Learning Domain-Driven Design":
            return {"results": [
                self._record(EN_ISBN, "Learning Domain-Driven Design", "en"),
            ]}
        return {"results": []}

    @staticmethod
    def _record(archive_id, title, language):
        return {
            "archive_id": archive_id,
            "title": title,
            "language": language,
            "content_format": "book",
            "authors": [],
            "publishers": [],
            "cover_url": f"/covers/urn:orm:book:{archive_id}/",
            "isbn": archive_id,
        }


def make_plugin(http_stub) -> BookPlugin:
    plugin = BookPlugin()
    plugin.kernel = type("K", (), {})()
    plugin.kernel.http = http_stub
    return plugin


class BookSearchTests(unittest.TestCase):
    def test_normalize(self):
        cases = [
            ("https://learning.oreilly.com/library/view/domeinqu-dong-she-ji-wohazimeyou-sohutoueanoshi"
             "-zhi-zhuang-toshi-ye-zhan-lue-wojie-bitukerushi-jian-ji-fa/9784814400737/", JA_ISBN),
            ("https://learning.oreilly.com/library/view/learning-domain-driven-design/9781098100124/",
             EN_ISBN),
            ("urn:orm:book:9784814400737", JA_ISBN),
            ("978-4-8144-0073-7", "9784814400737"),
            ("9781098100124", EN_ISBN),
            ("Learning Domain-Driven Design", None),
            ("", None),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                got = normalize_book_query(raw)
                self.assertEqual(got, expected)

        self.assertTrue(looks_like_book_id(JA_ISBN))
        self.assertTrue(looks_like_book_id("0596000278"))
        self.assertTrue(looks_like_book_id("059600027X"))
        self.assertFalse(looks_like_book_id("python books"))

    def test_search_english_isbn(self):
        stub = StubHttp()
        plugin = make_plugin(stub)
        results = plugin.search(EN_ISBN)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], EN_ISBN)
        self.assertEqual(len(stub.calls), 1, "first request should hit without probing")

    def test_search_japanese_isbn_probes_languages(self):
        stub = StubHttp()
        plugin = make_plugin(stub)
        results = plugin.search(JA_ISBN)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], JA_ISBN)
        self.assertEqual(results[0]["language"], "ja")

        first = urllib.parse.parse_qs(urllib.parse.urlparse(stub.calls[0]).query)
        second = urllib.parse.parse_qs(urllib.parse.urlparse(stub.calls[1]).query)
        self.assertNotIn("languages", first)
        self.assertEqual(second["languages"], ["ja"])

    def test_search_with_language_filter(self):
        stub = StubHttp()
        plugin = make_plugin(stub)
        results = plugin.search(EN_ISBN, language="ja")
        self.assertEqual(results, [])

        results = plugin.search(JA_ISBN, language="ja")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["language"], "ja")
        self.assertTrue(all("languages=ja" in u for u in stub.calls))

    def test_translations_found_via_title(self):
        stub = StubHttp()
        plugin = make_plugin(stub)

        def fake_epub(book_id):
            return {"title": "Learning Domain-Driven Design", "language": "en"}

        plugin._fetch_epub = fake_epub
        plugin.TRANSLATION_LANGUAGES = ["ja", "zh"]
        translations = plugin.find_translations(EN_ISBN)
        self.assertTrue(any(t["id"] == JA_ISBN for t in translations))
        self.assertTrue(all(t["language"] != "en" for t in translations))


if __name__ == "__main__":
    unittest.main()
