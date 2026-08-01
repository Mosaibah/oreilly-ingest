#!/usr/bin/env python3
"""
Source-Ready Markdown Combiner
Post-export utility to aggregate individual Markdown chapters into a single LLM-optimized file.
"""

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path


class SourceReadyCombiner:
    def __init__(self, input_dir: Path, overrides: dict = None):
        self.input_dir = input_dir.resolve()
        self.overrides = overrides or {}
        self.warnings = []
        self.chapters = []
        self.readme_link_count = 0
        self.included_chapters = []
        self.missing_chapters = []
        self.metadata = {
            "title": "Unknown Title",
            "authors": [],
            "publisher": "Unknown Publisher",
            "book_id": None,
            "category": self.overrides.get("category", "Technical"),
            "priority": self.overrides.get("priority", "Supporting"),
        }

    def run(self):
        """Execute the full combination pipeline."""
        print(f"[*] Starting combination in: {self.input_dir}")

        if not self.input_dir.is_dir():
            print(f"[!] Error: Path is not a directory: {self.input_dir}")
            sys.exit(1)

        readme_path = self.input_dir / "README.md"
        if not readme_path.exists():
            print(f"[!] Error: README.md not found in {self.input_dir}")
            sys.exit(1)

        # 1. Parse README.md
        self._parse_readme(readme_path)

        # 2. Check for .book_id
        self._detect_book_id()

        # 3. Apply Overrides
        if self.overrides.get("title"):
            self.metadata["title"] = self.overrides["title"]
        if self.overrides.get("author"):
            # Accept comma separated authors or single string
            auths = self.overrides["author"]
            self.metadata["authors"] = [a.strip() for a in auths.split(",")] if "," in auths else [auths]

        # 4. Generate Output Path
        safe_title = self._sanitize_filename(self.metadata["title"])
        output_filename = f"{safe_title}__SOURCE_READY.md"
        output_path = self.input_dir / output_filename
        manifest_path = self.input_dir / "source_ready_manifest.json"

        # Check for existing files
        if output_path.exists():
            print(f"[*] Overwriting existing file: {output_path.name}")
        if manifest_path.exists():
            print(f"[*] Overwriting existing manifest: {manifest_path.name}")

        # 5. Build Content
        full_content = self._assemble_content()

        if not self.included_chapters:
            print("[!] Error: No usable chapter files found in the source directory.")
            sys.exit(1)

        # 6. Write Files
        output_path.write_text(full_content, encoding="utf-8")
        self._write_manifest(manifest_path, output_filename)

        print(f"[+] Successfully generated: {output_filename}")
        print(f"[+] Successfully generated: {manifest_path.name}")
        print(f"[*] Included chapters: {len(self.included_chapters)} / {self.readme_link_count}")
        if self.missing_chapters:
            print(f"[*] Missing chapters: {len(self.missing_chapters)}")

        if self.warnings:
            print(f"\n[!] Warnings encountered ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")

    def _parse_readme(self, readme_path: Path):
        content = readme_path.read_text(encoding="utf-8")

        # Extract Title (First H1)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            self.metadata["title"] = title_match.group(1).strip()
        else:
            self.warnings.append("Could not find book title in README.md H1")

        # Extract Authors
        authors_match = re.search(r"\*\*Authors:\*\*\s*(.+)$", content, re.MULTILINE)
        if authors_match:
            self.metadata["authors"] = [a.strip() for a in authors_match.group(1).split(",")]
        else:
            self.warnings.append("Could not find authors in README.md")

        # Extract Publisher
        pub_match = re.search(r"\*\*Publishers?:\*\*\s*(.+)$", content, re.MULTILINE)
        if pub_match:
            self.metadata["publisher"] = pub_match.group(1).strip()
        else:
            self.warnings.append("Could not find publisher in README.md")

        # Extract Chapters
        chapters_section = re.split(r"##\s+Chapters", content, flags=re.IGNORECASE)
        if len(chapters_section) > 1:
            chapter_links = re.findall(r"-\s+\[([\s\S]+?)\]\((.+?\.md)\)", chapters_section[1])
            if not chapter_links:
                self.warnings.append("No chapter links found in README.md 'Chapters' section")
            
            self.readme_link_count = len(chapter_links)
            for i, (title, filename) in enumerate(chapter_links, 1):
                clean_title = " ".join(title.split())
                self.chapters.append({
                    "index": i,
                    "title": clean_title,
                    "filename": filename.strip()
                })
        else:
            self.readme_link_count = 0
            self.warnings.append("Could not find '## Chapters' section in README.md")

    def _detect_book_id(self):
        # Check parent directory for .book_id
        parent_id_file = self.input_dir.parent / ".book_id"
        if parent_id_file.exists():
            self.metadata["book_id"] = parent_id_file.read_text(encoding="utf-8").strip()
        else:
            self.warnings.append("Missing .book_id file in parent directory")

    def _assemble_content(self) -> str:
        processed_date = datetime.date.today().isoformat()
        
        # 1. YAML Frontmatter
        # We use json.dumps for safe quoting in YAML
        yaml_lines = [
            "---",
            f"source: {json.dumps(self.metadata['title'])}",
            f"author: {json.dumps(', '.join(self.metadata['authors']))}",
            "document_type: \"book\"",
            f"category: {json.dumps(self.metadata['category'])}",
            f"priority: {json.dumps(self.metadata['priority'])}",
            "use_for:",
            "  - \"retrieval inside ChatGPT Projects\"",
            "  - \"chapter-level source grounding inside one consolidated file\"",
            "do_not_use_for:",
            "  - \"current real-time information\"",
            "  - \"legal, medical, financial, or safety-critical advice unless independently verified\"",
            f"processed_date: \"{processed_date}\"",
            "pipeline_version: \"oreilly-ingest-v0.1\"",
            "conversion_profile: \"oreilly_native_markdown\"",
            "ocr_used: false",
            "notes: \"Generated directly from app HTML/XHTML export; consolidated and cleaned for LLM ingestion.\"",
            "---\n"
        ]
        
        # 2. Header and Usage Notes
        header_lines = [
            f"# {self.metadata['title']}\n",
            "## Source Usage Notes\n",
            "Use this source when you need deep technical context, specific code examples, or structured explanations from the book. Do not use for real-time data or safety-critical decisions without independent verification.\n",
            "## Book Metadata\n",
            f"- **Title:** {self.metadata['title']}",
            f"- **Authors:** {', '.join(self.metadata['authors'])}",
            f"- **Publisher:** {self.metadata['publisher']}",
            f"- **ISBN/ID:** {self.metadata['book_id'] or 'Unknown'}",
            "- **Source type:** O'Reilly native Markdown export",
            "- **Processing profile:** consolidated_source_ready_markdown",
            f"- **Processed Date:** {processed_date}\n"
        ]
        
        # 3. Table of Contents & 4. Chapters
        toc_lines = ["## Book Table of Contents\n"]
        anchors = {}
        seen_anchors = set()
        chapter_contents = []
        
        for ch in self.chapters:
            ch_path = self.input_dir / ch["filename"]
            
            if not ch_path.exists():
                self.warnings.append(f"Chapter file not found: {ch['filename']}")
                self.missing_chapters.append({
                    "index": ch["index"],
                    "title": ch["title"],
                    "filename": ch["filename"],
                    "reason": "Chapter file not found"
                })
                continue
                
            anchor = self._slugify_anchor(ch["title"], ch["index"])
            if anchor in seen_anchors:
                anchor = f"{anchor}-{ch['index']}"
            seen_anchors.add(anchor)
            anchors[ch["index"]] = anchor
            toc_lines.append(f"- [{ch['title']}](#{anchor})")
            
            content = ch_path.read_text(encoding="utf-8").strip()
            word_count = len(content.split())
            
            included_ch = ch.copy()
            included_ch["word_count"] = word_count
            included_ch["anchor"] = anchor
            self.included_chapters.append(included_ch)
            
            safe_marker_title = html.escape(ch["title"], quote=True)
            safe_marker_filename = html.escape(ch["filename"], quote=True)
            
            ch_block = [
                f'<a id="{anchor}"></a>\n',
                f'<!-- CHAPTER_START index="{ch["index"]}" title="{safe_marker_title}" original_filename="{safe_marker_filename}" -->\n',
                content,
                f'\n<!-- CHAPTER_END index="{ch["index"]}" -->\n',
                "---\n"
            ]
            chapter_contents.append("".join(ch_block))
            
        toc_lines.append("\n---\n")
        
        return "\n".join(yaml_lines) + "\n".join(header_lines) + "\n".join(toc_lines) + "\n".join(chapter_contents)

    def _write_manifest(self, manifest_path: Path, output_filename: str):
        manifest = {
            "source_ready_file": output_filename,
            "book_title": self.metadata["title"],
            "authors": self.metadata["authors"],
            "publisher": self.metadata["publisher"],
            "book_id": self.metadata["book_id"],
            "source_link_count": self.readme_link_count,
            "chapter_count": len(self.included_chapters),
            "processed_date": datetime.date.today().isoformat(),
            "chapters": self.included_chapters,
            "missing_chapters": self.missing_chapters,
            "warnings": self.warnings
        }
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a cross-platform filename."""
        name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
        name = re.sub(r'[<>|*?"\']', "_", name)
        name = re.sub(r"[\s_]+", "_", name)
        name = name.strip("_").strip()
        if not name:
            return "Unknown_Book"
        return name[:200]

    def _slugify_anchor(self, text: str, index: int) -> str:
        """Generate a stable anchor link from text."""
        text = text.lower()
        # Basic alphanumeric slug
        slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
        if not slug:
            # Handle non-ASCII or empty result
            if any(ord(c) > 127 for c in text):
                # Simple hash-like hex from string if non-ASCII
                slug = hex(hash(text) & 0xFFFFFFFF)[2:]
            else:
                slug = f"chapter-{index}"
        return slug


def main():
    parser = argparse.ArgumentParser(description="Consolidate Markdown chapters into a Source-Ready file.")
    parser.add_argument("input_dir", type=str, help="Path to the Markdown export directory")
    parser.add_argument("--title", type=str, help="Override book title")
    parser.add_argument("--author", type=str, help="Override authors (comma separated)")
    parser.add_argument("--category", type=str, default="Technical", help="Category for frontmatter")
    parser.add_argument("--priority", type=str, default="Supporting", help="Priority for frontmatter")

    args = parser.parse_args()
    
    combiner = SourceReadyCombiner(
        input_dir=Path(args.input_dir),
        overrides={
            "title": args.title,
            "author": args.author,
            "category": args.category,
            "priority": args.priority,
        }
    )
    combiner.run()


if __name__ == "__main__":
    main()
