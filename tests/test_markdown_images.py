import re
import tempfile
import unittest
from pathlib import Path

from plugins.html_processor import HtmlProcessorPlugin
from plugins.markdown import MarkdownPlugin


class MarkdownImageTests(unittest.TestCase):
    def test_generated_chapters_resolve_shared_images(self):
        with tempfile.TemporaryDirectory() as directory:
            book_dir = Path(directory)
            images_dir = book_dir / "OEBPS" / "Images"
            images_dir.mkdir(parents=True)
            image = images_dir / "figure.png"
            image.write_bytes(b"image fixture")

            html_processor = HtmlProcessorPlugin()
            chapters = []
            filenames = ["chapter.html", "part/chapter.xhtml", "part/section/chapter.html"]
            for filename in filenames:
                html, _ = html_processor.process(
                    '<div id="sbo-rt-content"><img src="https://example.com/figure.png" alt="Figure"></div>',
                    "test-book",
                    path_prefix="../" * filename.count("/"),
                )
                chapters.append((filename, "Chapter", html))

            MarkdownPlugin().generate_book({"title": "Test book"}, chapters, book_dir)

            for filename in filenames:
                with self.subTest(filename=filename):
                    md_path = (book_dir / "Markdown" / filename).with_suffix(".md")
                    targets = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md_path.read_text())
                    self.assertEqual(len(targets), 1)
                    self.assertEqual((md_path.parent / targets[0]).resolve(), image.resolve())
                    self.assertTrue((md_path.parent / targets[0]).is_file())

            self.assertFalse((book_dir / "Markdown" / "Images").exists())

    def test_explicit_current_directory_image_path(self):
        markdown = MarkdownPlugin().convert('<img src="./Images/figure.png" alt="Figure">')
        self.assertIn("![Figure](../OEBPS/Images/figure.png)", markdown)

    def test_other_image_urls_are_preserved(self):
        sources = [
            "https://example.com/Images/figure.png",
            "/Images/figure.png",
            "../OEBPS/Images/figure.png",
            "assets/figure.png",
        ]
        for source in sources:
            with self.subTest(source=source):
                markdown = MarkdownPlugin().convert(f'<img src="{source}" alt="Figure">')
                self.assertIn(f"![Figure]({source})", markdown)


if __name__ == "__main__":
    unittest.main()
