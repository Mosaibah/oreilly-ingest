import html
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .base import Plugin
from utils import sanitize_filename, slugify


class EpubPlugin(Plugin):
    def generate(
        self,
        book_info: dict,
        chapters: list[dict],
        toc: list[dict],
        output_dir: Path,
        css_files: list[str],
        cover_image: str | None = None,
    ) -> Path:
        oebps = output_dir / "OEBPS"
        oebps.mkdir(parents=True, exist_ok=True)
        (output_dir / "META-INF").mkdir(exist_ok=True)

        self._write_mimetype(output_dir)
        self._write_container_xml(output_dir)
        self._write_content_opf(oebps, book_info, chapters, css_files, cover_image)
        self._write_toc_ncx(oebps, book_info, toc)
        self._write_nav_xhtml(oebps, book_info, toc)

        # Use sanitized title for epub filename
        epub_name = sanitize_filename(book_info.get("title", book_info["id"]))
        epub_path = output_dir / f"{epub_name}.epub"
        self._create_epub_zip(output_dir, epub_path)

        # Clean up build artifacts
        self._cleanup_build_artifacts(output_dir)

        return epub_path

    def _cleanup_build_artifacts(self, output_dir: Path):
        """Remove intermediate EPUB build files after ZIP creation."""
        artifacts = [
            output_dir / "mimetype",
            output_dir / "META-INF",
            output_dir / "OEBPS",
        ]
        for artifact in artifacts:
            if artifact.is_file():
                artifact.unlink()
            elif artifact.is_dir():
                shutil.rmtree(artifact)

    def _write_mimetype(self, output_dir: Path):
        (output_dir / "mimetype").write_text("application/epub+zip")

    def _write_container_xml(self, output_dir: Path):
        content = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        (output_dir / "META-INF" / "container.xml").write_text(content)

    def _write_content_opf(
        self,
        oebps: Path,
        book_info: dict,
        chapters: list[dict],
        css_files: list[str],
        cover_image: str | None,
    ):
        title = html.escape(book_info.get("title", "Unknown"))
        authors = book_info.get("authors", [])
        isbn = book_info.get("isbn", book_info.get("id", "unknown"))
        description = html.escape(book_info.get("description", "")[:500])
        publishers = book_info.get("publishers", [])
        language = book_info.get("language", "en")
        pub_date = book_info.get("publication_date", "")

        author_xml = ""
        for author in authors:
            author_xml += f'    <dc:creator>{html.escape(author)}</dc:creator>\n'

        publisher_xml = ""
        for pub in publishers:
            publisher_xml += f"    <dc:publisher>{html.escape(pub)}</dc:publisher>\n"

        manifest_items = [
            '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        ]

        for i, ch in enumerate(chapters):
            filename = ch["filename"].replace(".html", ".xhtml")
            item_id = f"ch{i:03d}"
            manifest_items.append(
                f'    <item id="{item_id}" href="{filename}" media-type="application/xhtml+xml"/>'
            )

        for i, css in enumerate(css_files):
            manifest_items.append(
                f'    <item id="css{i:02d}" href="Styles/Style{i:02d}.css" media-type="text/css"/>'
            )

        cover_image_id = None
        if cover_image:
            cover_image_id = f"img_{Path(cover_image).stem}"

        images_dir = oebps / "Images"
        if images_dir.exists():
            for img_file in images_dir.iterdir():
                img_id = f"img_{img_file.stem}"
                media_type = self._get_image_media_type(img_file.suffix)
                properties = ""
                if cover_image_id and img_id == cover_image_id:
                    properties = ' properties="cover-image"'
                manifest_items.append(
                    f'    <item id="{img_id}" href="Images/{img_file.name}" media-type="{media_type}"{properties}/>'
                )

        spine_items = []
        for i, ch in enumerate(chapters):
            spine_items.append(f'    <itemref idref="ch{i:03d}"/>')

        modified_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        content = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:title>{title}</dc:title>
{author_xml}{publisher_xml}    <dc:description>{description}</dc:description>
    <dc:language>{language}</dc:language>
    <dc:identifier id="bookid">{isbn}</dc:identifier>
    <dc:date>{pub_date}</dc:date>
    <meta property="dcterms:modified">{modified_timestamp}</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine_items)}
  </spine>
</package>'''

        (oebps / "content.opf").write_text(content)

    def _write_toc_ncx(self, oebps: Path, book_info: dict, toc: list[dict]):
        title = html.escape(book_info.get("title", "Unknown"))
        isbn = book_info.get("isbn", book_info.get("id", "unknown"))
        authors = ", ".join(book_info.get("authors", ["Unknown"]))

        max_depth = self._get_max_depth(toc)
        nav_points, _ = self._build_nav_points(toc, 1)

        content = f'''<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta content="ID:ISBN:{isbn}" name="dtb:uid"/>
    <meta content="{max_depth}" name="dtb:depth"/>
    <meta content="0" name="dtb:totalPageCount"/>
    <meta content="0" name="dtb:maxPageNumber"/>
  </head>
  <docTitle>
    <text>{title}</text>
  </docTitle>
  <docAuthor>
    <text>{html.escape(authors)}</text>
  </docAuthor>
  <navMap>
{nav_points}
  </navMap>
</ncx>'''

        (oebps / "toc.ncx").write_text(content)

    def _write_nav_xhtml(self, oebps: Path, book_info: dict, toc: list[dict]):
        """Generate EPUB 3 navigation document (nav.xhtml)."""
        title = html.escape(book_info.get("title", "Unknown"))
        nav_items = self._build_nav_ol(toc)

        content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{title}</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
{nav_items}
    </ol>
  </nav>
</body>
</html>'''

        (oebps / "nav.xhtml").write_text(content)

    def _build_nav_points(self, toc_items: list[dict], play_order: int, indent: int = 4) -> tuple[str, int]:
        result = []
        spaces = " " * indent

        for item in toc_items:
            nav_id = item.get("fragment") or item.get("ourn", "").split(":")[-1].replace(".html", "")
            label = html.escape(item.get("title", ""))
            href = item.get("reference_id", "").split("-/")[-1] if item.get("reference_id") else ""
            href = href.replace(".html", ".xhtml")

            if item.get("fragment"):
                href = f"{href}#{item['fragment']}"

            result.append(f'{spaces}<navPoint id="{nav_id}" playOrder="{play_order}">')
            result.append(f'{spaces}  <navLabel><text>{label}</text></navLabel>')
            result.append(f'{spaces}  <content src="{href}"/>')

            play_order += 1

            children = item.get("children", [])
            if children:
                child_points, play_order = self._build_nav_points(children, play_order, indent + 2)
                result.append(child_points)

            result.append(f'{spaces}</navPoint>')

        return "\n".join(result), play_order

    def _build_nav_ol(self, toc_items: list[dict], indent: int = 6) -> str:
        """Build ordered list items for nav.xhtml navigation (EPUB 3)."""
        result = []
        spaces = " " * indent

        for item in toc_items:
            label = html.escape(item.get("title", ""))
            href = item.get("reference_id", "").split("-/")[-1] if item.get("reference_id") else ""
            href = href.replace(".html", ".xhtml")

            if item.get("fragment"):
                href = f"{href}#{item['fragment']}"

            children = item.get("children", [])
            if children:
                child_ol = self._build_nav_ol(children, indent + 2)
                result.append(f'{spaces}<li>')
                result.append(f'{spaces}  <a href="{href}">{label}</a>')
                result.append(f'{spaces}  <ol>')
                result.append(child_ol)
                result.append(f'{spaces}  </ol>')
                result.append(f'{spaces}</li>')
            else:
                result.append(f'{spaces}<li><a href="{href}">{label}</a></li>')

        return "\n".join(result)

    def _get_max_depth(self, toc_items: list[dict], current: int = 1) -> int:
        max_d = current
        for item in toc_items:
            children = item.get("children", [])
            if children:
                max_d = max(max_d, self._get_max_depth(children, current + 1))
        return max_d

    def _get_image_media_type(self, suffix: str) -> str:
        types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
        }
        return types.get(suffix.lower(), "application/octet-stream")

    def _create_epub_zip(self, output_dir: Path, epub_path: Path):
        with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zf:
            mimetype_path = output_dir / "mimetype"
            zf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)

            for file_path in output_dir.rglob("*"):
                if file_path.is_file() and file_path.name != "mimetype":
                    arcname = file_path.relative_to(output_dir)
                    if not str(arcname).endswith(".epub"):
                        zf.write(file_path, arcname)
