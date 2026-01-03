"""
Utility for extracting clean text from HTML content.
Used by PlainTextPlugin, JsonExportPlugin, and ChunkingPlugin.
"""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class CodeBlock:
    """Represents an extracted code block."""

    language: str
    code: str


@dataclass
class ExtractedContent:
    """Result of text extraction from HTML."""

    text: str
    code_blocks: list[CodeBlock] = field(default_factory=list)


class _HTMLTextExtractor(HTMLParser):
    """Internal HTML parser for text extraction."""

    BLOCK_TAGS = {
        "p",
        "div",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "tr",
        "blockquote",
        "section",
        "article",
        "header",
        "footer",
    }

    LIST_TAGS = {"ul", "ol"}
    CODE_TAGS = {"pre", "code"}

    def __init__(self):
        super().__init__()
        self.result = []
        self.code_blocks = []
        self._in_code = False
        self._code_buffer = []
        self._code_language = ""
        self._in_pre = False
        self._skip_content = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)

        if tag in ("script", "style"):
            self._skip_content = True
            return

        if tag == "pre":
            self._in_pre = True
            self._in_code = True
            self._code_language = self._detect_language(attrs_dict)
            self._code_buffer = []

        elif tag == "code" and not self._in_pre:
            self._in_code = True
            self._code_language = self._detect_language(attrs_dict)
            self._code_buffer = []

        elif tag in self.BLOCK_TAGS:
            self.result.append("\n")

        elif tag == "li":
            self.result.append("\n- ")

        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag: str):
        if tag in ("script", "style"):
            self._skip_content = False
            return

        if tag == "pre":
            if self._code_buffer:
                code = "".join(self._code_buffer).strip()
                if code:
                    self.code_blocks.append(
                        CodeBlock(language=self._code_language, code=code)
                    )
                    lang_marker = self._code_language if self._code_language else ""
                    self.result.append(f"\n```{lang_marker}\n{code}\n```\n")
            self._in_pre = False
            self._in_code = False
            self._code_buffer = []
            self._code_language = ""

        elif tag == "code" and not self._in_pre:
            code = "".join(self._code_buffer).strip()
            if code and "\n" not in code and len(code) < 100:
                self.result.append(f"`{code}`")
            elif code:
                self.code_blocks.append(
                    CodeBlock(language=self._code_language, code=code)
                )
                lang_marker = self._code_language if self._code_language else ""
                self.result.append(f"\n```{lang_marker}\n{code}\n```\n")
            self._in_code = False
            self._code_buffer = []
            self._code_language = ""

        elif tag in self.BLOCK_TAGS:
            self.result.append("\n")

    def handle_data(self, data: str):
        if self._skip_content:
            return

        if self._in_code:
            self._code_buffer.append(data)
        else:
            self.result.append(data)

    def _detect_language(self, attrs: dict) -> str:
        """Detect programming language from element attributes."""
        classes = attrs.get("class", "")
        if isinstance(classes, str):
            classes = classes.split()

        for cls in classes:
            cls_lower = cls.lower()
            if cls_lower.startswith("language-"):
                return cls_lower.replace("language-", "")
            if cls_lower.startswith("lang-"):
                return cls_lower.replace("lang-", "")
            if cls_lower.startswith("highlight-"):
                return cls_lower.replace("highlight-", "")

        data_lang = attrs.get("data-lang", "")
        if data_lang:
            return data_lang.lower()

        known_languages = {
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "csharp",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "sql",
            "html",
            "css",
            "bash",
            "shell",
            "json",
            "yaml",
            "xml",
        }
        for cls in classes:
            if cls.lower() in known_languages:
                return cls.lower()

        return ""

    def get_text(self) -> str:
        """Get the extracted text."""
        return "".join(self.result)


class TextExtractor:
    """
    Extracts plain text and code blocks from HTML content.

    Handles:
    - Stripping all HTML tags while preserving text
    - Extracting code blocks with language detection
    - Normalizing whitespace and line breaks
    - Preserving list structure as bullet points
    """

    def extract(self, html: str) -> ExtractedContent:
        """
        Extract plain text and code blocks from HTML.

        Args:
            html: Raw HTML content

        Returns:
            ExtractedContent with cleaned text and code blocks
        """
        parser = _HTMLTextExtractor()
        parser.feed(html)

        text = self._normalize_whitespace(parser.get_text())
        return ExtractedContent(text=text, code_blocks=parser.code_blocks)

    def extract_text_only(self, html: str) -> str:
        """
        Extract only plain text, formatting code blocks with markdown fences.

        Args:
            html: Raw HTML content

        Returns:
            Plain text with code blocks as ```lang ... ```
        """
        return self.extract(html).text

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace, normalize line breaks."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s+$", "", text, flags=re.MULTILINE)
        return text.strip()
