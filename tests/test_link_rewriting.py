"""Regression tests for internal chapter link rewriting.

Covers the HtmlProcessorPlugin (.html -> .xhtml normalization for the
internal HTML/EPUB representation, incl. fragments) and the MarkdownPlugin
(.xhtml/.html -> .md for Markdown output).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.html_processor import HtmlProcessorPlugin
from plugins.markdown import MarkdownPlugin


class TestHtmlProcessorLinks(unittest.TestCase):
    def setUp(self):
        self.plugin = HtmlProcessorPlugin()
        self.book_id = "9781098136796"

    def process_href(self, href: str) -> str:
        html = f'<div id="sbo-rt-content"><a href="{href}">x</a></div>'
        out, _ = self.plugin.process(html, self.book_id, skip_images=True)
        start = out.index('href="') + len('href="')
        return out[start:out.index('"', start)]

    def test_html_rewrite(self):
        for href in ("ch04.html", "./ch04.html", "../ch04.html"):
            self.assertEqual(self.process_href(href), href[:-5] + ".xhtml")

    def test_fragment_preserved(self):
        self.assertEqual(
            self.process_href("ch04.html#chapter_4_tool_use"),
            "ch04.xhtml#chapter_4_tool_use",
        )
        self.assertEqual(
            self.process_href("../ch04.html#anchor"), "../ch04.xhtml#anchor"
        )

    def test_external_untouched(self):
        self.assertEqual(
            self.process_href("https://example.com/page.html#anchor"),
            "https://example.com/page.html#anchor",
        )
        self.assertEqual(
            self.process_href("mailto:test@example.com"),
            "mailto:test@example.com",
        )

    def test_fragment_only_untouched(self):
        self.assertEqual(self.process_href("#anchor"), "#anchor")

    def test_non_chapter_link_untouched(self):
        self.assertEqual(self.process_href("Images/foo.png"), "Images/foo.png")


class TestMarkdownLinkTargets(unittest.TestCase):
    def setUp(self):
        self.plugin = MarkdownPlugin()

    def convert_href(self, href: str) -> str:
        html = f'<p><a href="{href}">x</a></p>'
        md = self.plugin.convert(html)
        return md[md.index("](") + 2 : md.index(")", md.index("]("))]

    def test_xhtml_to_md(self):
        self.assertEqual(self.convert_href("ch04.xhtml"), "ch04.md")

    def test_xhtml_fragment_to_md(self):
        self.assertEqual(
            self.convert_href("ch04.xhtml#chapter_4_tool_use"),
            "ch04.md#chapter_4_tool_use",
        )

    def test_html_fragment_to_md(self):
        self.assertEqual(
            self.convert_href("ch04.html#anchor"), "ch04.md#anchor"
        )

    def test_relative_paths(self):
        self.assertEqual(self.convert_href("./ch04.xhtml#anchor"), "./ch04.md#anchor")
        self.assertEqual(self.convert_href("../ch04.xhtml#anchor"), "../ch04.md#anchor")

    def test_fragment_only_untouched(self):
        self.assertEqual(self.convert_href("#anchor"), "#anchor")

    def test_external_untouched(self):
        self.assertEqual(
            self.convert_href("https://example.com/page.html#anchor"),
            "https://example.com/page.html#anchor",
        )
        self.assertEqual(
            self.convert_href("mailto:test@example.com"),
            "mailto:test@example.com",
        )

    def test_images_untouched(self):
        # _fix_image_paths intentionally prefixes ./Images/ (pre-existing behavior)
        self.assertEqual(self.convert_href("Images/foo.png"), "./Images/foo.png")
        self.assertEqual(self.convert_href("./Images/foo.png"), "./Images/foo.png")

    def test_full_pipeline(self):
        """End-to-end: chapter HTML -> markdown with .md cross-chapter link."""
        html = (
            '<div id="sbo-rt-content">'
            '<a href="ch08.html#chapter_8_from_one_agent_to_many">Chapter 8</a>'
            "</div>"
        )
        processed, _ = HtmlProcessorPlugin().process(
            html, "book123", skip_images=True
        )
        md = MarkdownPlugin().convert(processed)
        self.assertIn(
            "](ch08.xhtml#chapter_8_from_one_agent_to_many)".replace(".xhtml", ".md"),
            md,
        )
        self.assertNotIn(".html)", md)
        self.assertNotIn(".xhtml)", md)


if __name__ == "__main__":
    unittest.main()
