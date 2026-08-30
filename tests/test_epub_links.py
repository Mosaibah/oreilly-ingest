import posixpath
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from plugins.epub import EpubPlugin


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name in ("href", "src"):
            if name in attributes:
                self.references.append((tag, name, attributes[name]))


class EpubLinkRewriteTests(unittest.TestCase):
    def setUp(self):
        self.plugin = EpubPlugin()

    def test_rewrites_mapped_links_and_preserves_suffixes(self):
        resource_names = {
            "chapter.html": "chapter.xhtml",
            "notes.html": "notes.xhtml",
            "appendix.xml": "appendix.xml",
        }
        content = '''
<a href="chapter.html#note">note</a>
<a href="notes.html?view=all#return">back</a>
<a href="appendix.xml#entry">appendix</a>
'''

        rewritten = self.plugin._rewrite_resource_references(
            content, "chapter.xhtml", resource_names
        )

        parser = ReferenceParser()
        parser.feed(rewritten)
        self.assertEqual(
            [reference for _, _, reference in parser.references],
            [
                "chapter.xhtml#note",
                "notes.xhtml?view=all#return",
                "appendix.xml#entry",
            ],
        )

    def test_rewrites_forward_footnote_and_backlink(self):
        resource_names = {
            "text/chapter.html": "text/chapter.xhtml",
            "notes/footnotes.html": "notes/footnotes.xhtml",
        }

        forward = self.plugin._rewrite_resource_references(
            '<a href="../notes/footnotes.html#note-1">1</a>',
            "text/chapter.xhtml",
            resource_names,
        )
        back = self.plugin._rewrite_resource_references(
            '<a href="../text/chapter.html#note-ref-1">return</a>',
            "notes/footnotes.xhtml",
            resource_names,
        )

        self.assertIn('href="../notes/footnotes.xhtml#note-1"', forward)
        self.assertIn('href="../text/chapter.xhtml#note-ref-1"', back)

    def test_ignores_nonlocal_and_nonmapped_references(self):
        resource_names = {"chapter.html": "chapter.xhtml"}
        content = '''
<a href="https://example.com/chapter.html#note">external</a>
<a href="//example.com/chapter.html">protocol relative</a>
<a href="mailto:reader@example.com">email</a>
<a href="#note">fragment</a>
<img src="Images/chapter.html"/>
<link href="Styles/book.css" rel="stylesheet"/>
<code>literal href="chapter.html"</code>
'''

        rewritten = self.plugin._rewrite_resource_references(
            content, "chapter.xhtml", resource_names
        )

        self.assertEqual(rewritten, content)


class GeneratedEpubLinkTests(unittest.TestCase):
    def test_all_relative_references_target_packaged_resources(self):
        plugin = EpubPlugin()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            oebps = output_dir / "OEBPS"
            (oebps / "text").mkdir(parents=True)
            (oebps / "notes").mkdir()
            (oebps / "Images").mkdir()
            (oebps / "Images" / "cover.png").write_bytes(b"image")
            (oebps / "text" / "chapter.xhtml").write_text(
                '<a href="../notes/footnotes.html?mode=read#note-1">1</a>'
                '<img src="../Images/cover.png"/>',
                encoding="utf-8",
            )
            (oebps / "notes" / "footnotes.xhtml").write_text(
                '<a href="../text/chapter.html#note-ref-1">return</a>',
                encoding="utf-8",
            )

            chapters = [
                {"filename": "text/chapter.html"},
                {"filename": "notes/footnotes.html"},
            ]
            toc = [
                {
                    "title": "Chapter",
                    "reference_id": "urn:orm:book:test-/text/chapter.html",
                    "fragment": "note-ref-1",
                }
            ]
            epub_path = plugin.generate(
                book_info={"id": "test", "title": "Test Book"},
                chapters=chapters,
                toc=toc,
                output_dir=output_dir,
                css_files=[],
            )

            with zipfile.ZipFile(epub_path) as epub:
                packaged = set(epub.namelist())
                broken = []
                for name in packaged:
                    if not name.endswith((".xhtml", ".ncx", ".opf")):
                        continue
                    parser = ReferenceParser()
                    parser.feed(epub.read(name).decode())
                    for _, _, reference in parser.references:
                        parsed = urlsplit(reference)
                        if parsed.scheme or parsed.netloc or not parsed.path:
                            continue
                        target = posixpath.normpath(
                            posixpath.join(posixpath.dirname(name), parsed.path)
                        )
                        if target not in packaged:
                            broken.append((name, reference))

            self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
