import re
from pathlib import Path
from markdownify import markdownify as md
from .base import Plugin


class MarkdownPlugin(Plugin):
    def convert(self, html: str, title: str = "") -> str:
        markdown = md(
            html,
            heading_style="ATX",
            code_language_callback=self._detect_language,
            strip=["script", "style"],
        )

        markdown = self._fix_image_paths(markdown)
        markdown = self._clean_whitespace(markdown)

        if title and not markdown.startswith("#"):
            markdown = f"# {title}\n\n{markdown}"

        return markdown

    def save_chapter(self, html: str, title: str, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = self.convert(html, title)
        output_path.write_text(markdown)

    def generate_book(
        self,
        book_info: dict,
        chapters: list[tuple[str, str, str]],
        output_dir: Path,
    ):
        md_dir = output_dir / "Markdown"
        md_dir.mkdir(parents=True, exist_ok=True)

        readme = f"# {book_info.get('title', 'Unknown')}\n\n"
        readme += f"**Authors:** {', '.join(book_info.get('authors', []))}\n\n"
        readme += f"**Publishers:** {', '.join(book_info.get('publishers', []))}\n\n"
        readme += "## Chapters\n\n"

        for filename, title, html in chapters:
            md_filename = filename.replace(".html", ".md").replace(".xhtml", ".md")
            self.save_chapter(html, title, md_dir / md_filename)
            readme += f"- [{title}]({md_filename})\n"

        (md_dir / "README.md").write_text(readme)

    def _detect_language(self, el):
        classes = el.get("class", [])
        if isinstance(classes, str):
            classes = classes.split()

        for cls in classes:
            if cls.startswith("language-"):
                return cls.replace("language-", "")
            if cls.startswith("lang-"):
                return cls.replace("lang-", "")

        return None

    def _fix_image_paths(self, markdown: str) -> str:
        return re.sub(r"\]\(Images/", "](./Images/", markdown)

    def _clean_whitespace(self, markdown: str) -> str:
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return markdown.strip() + "\n"
