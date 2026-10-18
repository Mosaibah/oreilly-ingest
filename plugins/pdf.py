"""PDF generation plugin using WeasyPrint."""

import html
import posixpath
import re
import sys
from pathlib import Path

from utils.files import sanitize_filename

from .base import Plugin


def _patch_macos_homebrew_dylib_loading():
    """Prefer real Homebrew .dylib paths for libraries loaded by WeasyPrint."""
    if sys.platform != "darwin":
        return

    import cffi

    original_dlopen = cffi.FFI.dlopen
    if getattr(original_dlopen, "_oreilly_homebrew_dylib_patch", False):
        return

    brew_lib_dirs = (Path("/opt/homebrew/lib"), Path("/usr/local/lib"))
    aliases = {
        "libpango-1.0-0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "pango-1.0-0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "pango-1.0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "libpangoft2-1.0-0": (
            "libpangoft2-1.0.dylib",
            "libpangoft2-1.0.0.dylib",
        ),
        "pangoft2-1.0-0": (
            "libpangoft2-1.0.dylib",
            "libpangoft2-1.0.0.dylib",
        ),
        "pangoft2-1.0": (
            "libpangoft2-1.0.dylib",
            "libpangoft2-1.0.0.dylib",
        ),
        "libgobject-2.0-0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "gobject-2.0-0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "gobject-2.0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "libharfbuzz-0": ("libharfbuzz.dylib", "libharfbuzz.0.dylib"),
        "harfbuzz-0.0": ("libharfbuzz.dylib", "libharfbuzz.0.dylib"),
        "libharfbuzz-subset-0": (
            "libharfbuzz-subset.dylib",
            "libharfbuzz-subset.0.dylib",
        ),
        "harfbuzz-subset-0.0": (
            "libharfbuzz-subset.dylib",
            "libharfbuzz-subset.0.dylib",
        ),
        "libfontconfig-1": ("libfontconfig.dylib", "libfontconfig.1.dylib"),
        "fontconfig-1": ("libfontconfig.dylib", "libfontconfig.1.dylib"),
    }

    def dlopen(self, name, flags=0):
        if isinstance(name, str) and name in aliases:
            for lib_dir in brew_lib_dirs:
                for filename in aliases[name]:
                    dylib_path = lib_dir / filename
                    if dylib_path.exists():
                        return original_dlopen(self, str(dylib_path), flags)

        return original_dlopen(self, name, flags)

    dlopen._oreilly_homebrew_dylib_patch = True
    cffi.FFI.dlopen = dlopen


class PdfPlugin(Plugin):
    """Generates PDF from downloaded book content using WeasyPrint."""

    def __init__(self):
        self._weasyprint = None

    @property
    def weasyprint(self):
        """Lazy import WeasyPrint to avoid import errors if not installed."""
        if self._weasyprint is None:
            try:
                _patch_macos_homebrew_dylib_loading()
                import weasyprint
                self._weasyprint = weasyprint
            except ImportError as e:
                raise ImportError(
                    "WeasyPrint is required for PDF generation. "
                    "Install with: pip install weasyprint\n"
                    "System dependencies (macOS): brew install pango\n"
                    "System dependencies (Ubuntu): apt install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0"
                ) from e
        return self._weasyprint

    def generate(
        self,
        book_info: dict,
        chapters: list[dict],
        toc: list[dict],
        output_dir: Path,
        css_files: list[str],
        cover_image: str | None = None,
    ) -> Path:
        """
        Generate a single PDF containing all chapters.

        Args:
            book_info: Book metadata (title, authors, isbn, publisher)
            chapters: List of chapter dicts with filename, title, order
            toc: Nested table of contents structure
            output_dir: Path to output/{book_id}/ directory
            css_files: List of CSS filenames in OEBPS/Styles/
            cover_image: Optional cover image filename in OEBPS/Images/

        Returns:
            Path to generated PDF file
        """
        output_dir = Path(output_dir)
        oebps = output_dir / "OEBPS"

        html_content = self._build_combined_html(
            book_info=book_info,
            chapters=chapters,
            toc=toc,
            oebps=oebps,
            css_files=css_files,
            cover_image=cover_image,
        )

        title = book_info.get("title", "book")
        safe_title = sanitize_filename(title)
        pdf_path = output_dir / f"{safe_title}.pdf"

        html_doc = self.weasyprint.HTML(
            string=html_content,
            base_url=str(oebps),
        )
        html_doc.write_pdf(str(pdf_path))

        return pdf_path

    def generate_chapters(
        self,
        book_info: dict,
        chapters: list[dict],
        output_dir: Path,
        css_files: list[str],
    ) -> list[Path]:
        """
        Generate individual PDF files for each chapter.

        Args:
            book_info: Book metadata (title, authors, isbn, publisher)
            chapters: List of chapter dicts with filename, title, order
            output_dir: Path to output/{book_id}/ directory
            css_files: List of CSS filenames in OEBPS/Styles/

        Returns:
            List of paths to generated PDF files
        """
        output_dir = Path(output_dir)
        oebps = output_dir / "OEBPS"
        pdf_dir = output_dir / "PDF"
        pdf_dir.mkdir(exist_ok=True)

        # Load CSS
        print_css = self._get_print_css()
        original_css = self._load_css_files(oebps, css_files)

        pdf_paths = []

        for i, chapter in enumerate(chapters):
            xhtml_path = oebps / chapter["filename"].replace(".html", ".xhtml")
            if not xhtml_path.exists():
                continue

            body = self._extract_chapter_body(xhtml_path, oebps)
            chapter_title = self._escape_html(chapter.get("title", f"Chapter {i+1}"))

            chapter_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{chapter_title}</title>
    <style>{print_css}</style>
    <style>{original_css}</style>
</head>
<body>
    <section class="chapter">
        <h1 class="chapter-title">{chapter_title}</h1>
        {body}
    </section>
</body>
</html>'''

            # Create filename with order prefix
            safe_title = sanitize_filename(chapter.get("title", f"chapter_{i+1}"))
            pdf_filename = f"{i+1:03d}_{safe_title}.pdf"
            pdf_path = pdf_dir / pdf_filename

            html_doc = self.weasyprint.HTML(
                string=chapter_html,
                base_url=str(oebps),
            )
            html_doc.write_pdf(str(pdf_path))
            pdf_paths.append(pdf_path)

        return pdf_paths

    def _build_combined_html(
        self,
        book_info: dict,
        chapters: list[dict],
        toc: list[dict],
        oebps: Path,
        css_files: list[str],
        cover_image: str | None,
    ) -> str:
        """Build single HTML document combining all chapters."""
        print_css = self._get_print_css()
        original_css = self._load_css_files(oebps, css_files)

        cover_html = self._generate_cover_html(book_info, cover_image)
        toc_html = self._generate_toc_html(toc, chapters)

        chapters_html_parts = []

        for chapter in chapters:
            xhtml_path = oebps / chapter["filename"].replace(".html", ".xhtml")
            if not xhtml_path.exists():
                continue

            body = self._extract_chapter_body(xhtml_path, oebps)
            chapter_id = Path(chapter["filename"]).stem
            chapter_title = self._escape_html(chapter.get("title", ""))

            chapters_html_parts.append(f'''
    <section class="chapter" id="{chapter_id}">
        <h1 class="chapter-title">{chapter_title}</h1>
        {body}
    </section>''')

        chapters_html = "\n".join(chapters_html_parts)
        title = self._escape_html(book_info.get("title", "Untitled"))

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>{print_css}</style>
    <style>{original_css}</style>
</head>
<body>
    {cover_html}
    {toc_html}
    {chapters_html}
</body>
</html>'''

    def _generate_cover_html(
        self,
        book_info: dict,
        cover_image: str | None,
    ) -> str:
        """Generate HTML for cover page."""
        title = self._escape_html(book_info.get("title", "Untitled"))
        authors = ", ".join(book_info.get("authors", []))
        authors = self._escape_html(authors) if authors else ""
        publishers = ", ".join(book_info.get("publishers", []))
        publishers = self._escape_html(publishers) if publishers else ""

        cover_img = ""
        if cover_image:
            cover_img = f'<img src="Images/{cover_image}" alt="Cover">'

        author_html = f'<p class="authors">{authors}</p>' if authors else ""
        publisher_html = f'<p class="publisher">{publishers}</p>' if publishers else ""

        return f'''
    <section class="cover-page">
        {cover_img}
        <h1>{title}</h1>
        {author_html}
        {publisher_html}
    </section>'''

    def _generate_toc_html(self, toc: list[dict], chapters: list[dict]) -> str:
        """Generate HTML table of contents with internal links."""
        if not toc:
            return ""

        def render_item(item: dict) -> str:
            title = self._escape_html(item.get("title", "Untitled"))

            # Get href from reference_id and convert to chapter ID
            href = item.get("reference_id", "")
            if href:
                # Extract filename from reference like "urn:orm:book:123/-/ch001.html"
                if "-/" in href:
                    href = href.split("-/")[-1]
                chapter_id = Path(href).stem
                link = f'<a href="#{chapter_id}">{title}</a>'
            else:
                link = title

            children_html = ""
            if item.get("children"):
                children_items = "".join(
                    f"<li>{render_item(child)}</li>"
                    for child in item["children"]
                )
                children_html = f"<ul>{children_items}</ul>"

            return f"{link}{children_html}"

        toc_items = "".join(f"<li>{render_item(item)}</li>" for item in toc)

        return f'''
    <section class="toc-page">
        <h2>Table of Contents</h2>
        <ul>{toc_items}</ul>
    </section>'''

    def _extract_chapter_body(self, xhtml_path: Path, oebps: Path) -> str:
        """Extract body content from XHTML file, with URLs relative to OEBPS."""
        content = xhtml_path.read_text(encoding="utf-8")

        # Find <body> content
        body_match = re.search(
            r'<body[^>]*>(.*?)</body>',
            content,
            re.DOTALL | re.IGNORECASE,
        )

        body = body_match.group(1) if body_match else content

        # Chapters may live in a subdirectory (e.g. OEBPS/Text/) and reference
        # assets as "../Images/x.png". The combined document is rendered with
        # OEBPS as its base, so re-anchor those references to OEBPS.
        chapter_dir = xhtml_path.parent.relative_to(oebps).as_posix()
        return re.sub(
            r'(<img\b[^>]*?\ssrc=)(["\'])(.*?)\2',
            lambda m: f"{m.group(1)}{m.group(2)}{self._rebase_url(m.group(3), chapter_dir)}{m.group(2)}",
            body,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def _rebase_url(self, url: str, from_dir: str) -> str:
        """Rewrite a URL relative to OEBPS/from_dir so it is relative to OEBPS."""
        if from_dir in ("", ".") or re.match(r'^([a-z][a-z0-9+.-]*:|/|#)', url, re.IGNORECASE):
            return url
        return posixpath.normpath(posixpath.join(from_dir, url))

    def _load_css_files(self, oebps: Path, css_files: list[str]) -> str:
        """Load and concatenate CSS files."""
        css_parts = []
        styles_dir = oebps / "Styles"

        for i, _ in enumerate(css_files):
            css_path = styles_dir / f"Style{i:02d}.css"
            if css_path.exists():
                # The CSS is inlined into the document, so url() references
                # relative to Styles/ must be re-anchored to OEBPS.
                css_parts.append(re.sub(
                    r'url\(\s*(["\']?)([^)"\']+)\1\s*\)',
                    lambda m: f'url("{self._rebase_url(m.group(2).strip(), "Styles")}")',
                    css_path.read_text(encoding="utf-8"),
                ))

        return "\n".join(css_parts)

    def _get_print_css(self) -> str:
        """Return print-specific CSS for PDF generation."""
        css_path = Path(__file__).parent / "pdf_styles" / "print.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")

        # Fallback inline CSS if file doesn't exist
        return self._get_fallback_print_css()

    def _get_fallback_print_css(self) -> str:
        """Inline fallback CSS for print styling."""
        return '''
@page {
    size: Letter;
    margin: 1in 0.75in;
    @bottom-center { content: counter(page); font-size: 9pt; }
}
@page :first {
    @bottom-center { content: none; }
}
.cover-page {
    page-break-after: always;
    text-align: center;
    padding-top: 2in;
}
.cover-page img { max-width: 100%; max-height: 6in; }
.cover-page h1 { font-size: 24pt; margin-top: 1in; }
.cover-page .authors { font-size: 14pt; color: #333; margin-top: 0.5in; }
.toc-page { page-break-after: always; }
.toc-page h2 { font-size: 18pt; margin-bottom: 1em; }
.toc-page ul { list-style: none; padding: 0; }
.toc-page li { margin: 0.5em 0; }
.toc-page a { color: #000; text-decoration: none; }
.chapter { page-break-before: always; }
.chapter:first-of-type { page-break-before: auto; }
.chapter-title {
    font-size: 20pt;
    margin-bottom: 1em;
    bookmark-level: 1;
    bookmark-label: content();
}
img { max-width: 100%; height: auto; }
figure { page-break-inside: avoid; }
pre, code {
    font-family: "Courier New", monospace;
    font-size: 9pt;
    background: #f5f5f5;
    padding: 0.5em;
    page-break-inside: avoid;
}
table { page-break-inside: avoid; border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 0.5em; }
p { orphans: 3; widows: 3; }
'''

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return html.escape(str(text)) if text else ""
