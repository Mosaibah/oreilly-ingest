import re
from bs4 import BeautifulSoup
from .base import Plugin


class HtmlProcessorPlugin(Plugin):
    def process(self, html: str, book_id: str, skip_images: bool = False) -> tuple[str, list[str]]:
        soup = BeautifulSoup(html, "lxml")
        images_found = []

        content_div = soup.find("div", id="sbo-rt-content")
        if not content_div:
            content_div = soup.body or soup

        self._convert_svg_images(content_div)

        if skip_images:
            self._remove_images(content_div)
            images_found = []
        else:
            images_found = self._rewrite_image_links(content_div)

        self._rewrite_href_links(content_div, book_id)
        self._handle_data_template_styles(content_div)

        return str(content_div), images_found

    def _remove_images(self, soup) -> None:
        """Remove all img tags from content"""
        for img in soup.find_all("img"):
            img.decompose()

    def _convert_svg_images(self, soup):
        for image_tag in soup.find_all("image"):
            href = image_tag.get("href") or image_tag.get("xlink:href")
            if not href:
                continue

            img_tag = soup.new_tag("img", src=href)
            parent = image_tag.parent
            if parent and parent.name == "svg":
                parent.replace_with(img_tag)
            else:
                image_tag.replace_with(img_tag)

    def _rewrite_image_links(self, soup) -> list[str]:
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue

            filename = src.split("/")[-1]
            img["src"] = f"Images/{filename}"
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

            if href.endswith(".html"):
                href = href.replace(".html", ".xhtml")

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
