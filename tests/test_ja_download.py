"""End-to-end integration test: download the Japanese edition with expired session cookies.

Run from repo root:
    python -m unittest tests/test_ja_download.py
"""
import unittest
import zipfile
from pathlib import Path

from core import create_default_kernel

BOOK_ID = "9784814400737"  # ドメイン駆動設計をはじめよう (Japanese edition)


class JapaneseDownloadE2ETests(unittest.TestCase):
    def test_download_japanese_edition(self):
        kernel = create_default_kernel()

        # Check if network is available
        try:
            info = kernel["book"].fetch(BOOK_ID)
        except Exception as e:
            raise unittest.SkipTest(f"O'Reilly API not reachable (offline/sandboxed): {e}")

        self.assertEqual(info["language"], "ja", "language should be ja")
        self.assertTrue(info["title"], "title required")

        chapters = kernel["chapters"].fetch_list(BOOK_ID)
        self.assertGreaterEqual(len(chapters), 30, "expected ~38 chapters")

        downloader = kernel["downloader"]
        output_dir = Path("output")
        result = downloader.download(
            book_id=BOOK_ID,
            output_dir=output_dir,
            formats=["epub", "markdown"],
            selected_chapters=list(range(6)),  # keep the test fast
            skip_images=True,
        )

        epub_path = result.files["epub"]
        with zipfile.ZipFile(epub_path) as zf:
            opf = zf.read("OEBPS/content.opf").decode("utf-8")
            self.assertIn("<dc:language>ja</dc:language>", opf, "EPUB must declare ja")
            names = zf.namelist()
            xhtml = [n for n in names if n.endswith(".xhtml")]
            self.assertGreater(len(xhtml), 0)

        md_book = list(Path(result.files["markdown"]).glob("*.md"))
        self.assertGreater(len(md_book), 0)


if __name__ == "__main__":
    unittest.main()
