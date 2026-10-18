import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from .base import Plugin


class HtmlProcessorPlugin(Plugin):
    def process(self, html: str, book_id: str, skip_images: bool = False, path_prefix: str = "") -> tuple[str, list[str]]:
        soup = BeautifulSoup(html, "lxml")
        images_found = []

        content_div = soup.find("div", id="sbo-rt-content")
        if not content_div:
            content_div = soup.body or soup

        self._convert_svg_images(content_div, soup)

        if skip_images:
            self._remove_images(content_div)
            images_found = []
        else:
            images_found = self._rewrite_image_links(content_div, path_prefix)

        self._rewrite_href_links(content_div, book_id)
        self._handle_data_template_styles(content_div)

        return str(content_div), images_found

    def _remove_images(self, soup) -> None:
        """Remove all img tags from content"""
        for img in soup.find_all("img"):
            img.decompose()

    def _convert_svg_images(self, content_div, soup):
        for image_tag in content_div.find_all("image"):
            href = image_tag.get("href") or image_tag.get("xlink:href")
            if not href:
                continue

            img_tag = soup.new_tag("img", src=href)
            parent = image_tag.parent
            if parent and parent.name == "svg":
                parent.replace_with(img_tag)
            else:
                image_tag.replace_with(img_tag)

    def _rewrite_image_links(self, soup, path_prefix: str = "") -> list[str]:
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue

            filename = src.split("/")[-1]
            img["src"] = f"{path_prefix}Images/{filename}"
            images.append(src)

        return images

    def _rewrite_href_links(self, soup, book_id: str):
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if href.startswith("mailto:"):
                continue

            if href.startswith(("http://", "https://")):
                if book_id in href:
                    path = href.split(book_id)[-1].lstrip("/")
                    href = path
                else:
                    continue

            # Rewrite only the path extension; preserve fragment/query intact
            # (e.g. ch04.html#anchor -> ch04.xhtml#anchor)
            parts = urlsplit(href)
            if parts.path.endswith(".html"):
                a["href"] = urlunsplit(
                    parts._replace(path=parts.path[:-5] + ".xhtml")
                )
            else:
                a["href"] = href

    def _handle_data_template_styles(self, soup):
        for style in soup.find_all("style"):
            if style.has_attr("data-template"):
                style.string = style["data-template"]
                del style["data-template"]

    def wrap_xhtml(self, content: str, css_files: list[str], title: str = "") -> str:
        css_links = "\n".join(
            f'<link href="{css}" rel="stylesheet" type="text/css"/>'
            for css in css_files
        )

        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
<title>{title}</title>
{css_links}
<style type="text/css">
body{{margin:1em;background-color:transparent!important;}}
#sbo-rt-content *{{text-indent:0pt!important;}}
</style>
</head>
<body>
{content}
</body>
</html>'''

    def inline_css_content_images(self, oebps: Path):
        """Replace CSS content:url() pseudo-element images with inline <img> tags.

        Apple Books doesn't support content:url() in pseudo-elements.
        This parses downloaded CSS for such rules, copies the referenced images
        to Images/ (so they appear in the manifest), injects <img> tags into
        matching XHTML elements, and strips the CSS rules to avoid duplicates.
        """
        styles_dir = oebps / "Styles"
        images_dir = oebps / "Images"
        if not styles_dir.exists():
            return

        # Collect rules from all CSS files
        rules = []  # (selector, img_src_relative_to_xhtml, is_before)
        for css_path in sorted(styles_dir.glob("Style*.css")):
            css_text = css_path.read_text(encoding="utf-8")
            found = self._extract_css_content_url_rules(css_text, styles_dir, images_dir)
            if found:
                rules.extend(found)
                # Strip content:url() from CSS to avoid duplicates
                cleaned = re.sub(
                    r'content\s*:\s*url\([^)]+\)',
                    'content:""',
                    css_text,
                )
                css_path.write_text(cleaned, encoding="utf-8")

        if not rules:
            return

        # Inject <img> into each XHTML file
        for xhtml_path in oebps.glob("*.xhtml"):
            if xhtml_path.name in ("nav.xhtml", "toc.ncx"):
                continue
            self._inject_images_into_xhtml(xhtml_path, rules)

    def _extract_css_content_url_rules(
        self, css_text: str, styles_dir: Path, images_dir: Path
    ) -> list[tuple[str, str, bool]]:
        """Extract (css_selector, image_src, is_before) from content:url() rules.

        Copies referenced images to Images/ so they appear in the EPUB manifest.
        """
        results = []
        for match in re.finditer(
            r'([^{}]+?)\s*\{[^}]*?content\s*:\s*url\(["\']?([^)"\']+)["\']?\)[^}]*\}',
            css_text,
        ):
            selector_raw = match.group(1).strip()
            url_ref = match.group(2)
            if url_ref.startswith("data:"):
                continue

            is_before = ":before" in selector_raw

            # Strip pseudo-element to get the base selector
            selector = re.sub(r"::?(before|after)", "", selector_raw).strip()
            if not selector:
                continue

            # Copy image from Styles/css_assets/ to Images/ for manifest inclusion
            src_file = styles_dir / url_ref
            filename = Path(url_ref).name
            if src_file.exists():
                images_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, images_dir / filename)

            # Reference from Images/ (relative to XHTML in OEBPS)
            img_src = f"Images/{filename}"

            # Handle comma-separated selectors
            for sel in selector.split(","):
                sel = sel.strip()
                if sel:
                    results.append((sel, img_src, is_before))

        return results

    def _inject_images_into_xhtml(
        self,
        xhtml_path: Path,
        rules: list[tuple[str, str, bool]],
    ):
        """Inject <img> tags into XHTML for matching CSS content:url() rules."""
        text = xhtml_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        modified = False

        for selector, img_src, is_before in rules:
            try:
                elements = soup.select(selector)
            except Exception:
                continue

            for el in elements:
                img_tag = soup.new_tag("img", src=img_src, alt="")
                img_tag["style"] = "max-width:100%;display:block;margin:0 auto"
                if is_before:
                    el.insert(0, img_tag)
                else:
                    el.append(img_tag)
                modified = True

        if modified:
            xhtml_path.write_text(str(soup), encoding="utf-8")

    def detect_cover_image(self, soup) -> str | None:
        for img in soup.find_all("img"):
            src = img.get("src", "").lower()
            alt = img.get("alt", "").lower()
            img_id = img.get("id", "").lower()
            img_class = " ".join(img.get("class", [])).lower()

            if any("cover" in x for x in [src, alt, img_id, img_class]):
                return img.get("src")

        for div in soup.find_all("div"):
            div_id = div.get("id", "").lower()
            div_class = " ".join(div.get("class", [])).lower()

            if "cover" in div_id or "cover" in div_class:
                img = div.find("img")
                if img:
                    return img.get("src")

        return None
