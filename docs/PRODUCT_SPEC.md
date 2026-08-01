# Product Specification: Source-Ready Markdown

## Product Goal
Provide a "Single Source of Truth" Markdown file for an entire book that maximizes LLM retrieval performance within ChatGPT Projects.

## Primary User Workflow
1. User identifies a book via the existing web UI or CLI.
2. User selects "Markdown" as the export format.
3. The system processes the book and generates an output folder.
4. User finds `<Book_Title>__SOURCE_READY.md` in the output.
5. User uploads this single file to a ChatGPT Project.

## Input Types
- O'Reilly Book Metadata (API v2).
- Processed HTML/XHTML chapter content.
- Local images (referenced, not embedded).

## Desired Output Structure
The output for a book remains unchanged for existing files, with new artifacts added by the combiner:
```text
output/<book_name>/Markdown/
├── chapter_01.md
├── chapter_02.md
├── ...
├── README.md
├── <Book_Title>__SOURCE_READY.md (NEW)
└── source_ready_manifest.json (NEW)
```

## Consolidated .md Structure

### 1. YAML Frontmatter
```yaml
---
source: "<book title>"
author: "<authors>"
document_type: "book"
category: "<category>"
priority: "<Core | Supporting | Reference>"
use_for:
  - "retrieval inside ChatGPT Projects"
  - "chapter-level source grounding"
do_not_use_for:
  - "current real-time information"
processed_date: "YYYY-MM-DD"
pipeline_version: "native-md-export-v0.1"
conversion_profile: "native_markdown_export"
ocr_used: false
notes: "Generated from native HTML; consolidated for LLM ingestion via post-export combiner."
---
```

### 2. Header & Usage Notes
- `# <Book Title>`
- `## Source Usage Notes` (Static placeholders for user guidance).

### 3. Book Table of Contents
- A list of internal Markdown links to chapter anchors.

### 4. Content with Chapter Markers
```markdown
---
<!-- CHAPTER_START index="1" title="..." original_filename="..." -->
# Chapter 1. <Title>
<content>
<!-- CHAPTER_END index="1" -->
---
```

## Manifest Expectations
A `manifest.json` file containing:
- Book metadata (ID, ISBN, Title, Authors).
- List of chapters with titles and filenames.
- Checksum or timestamp of generation.

## README Expectations
The `README.md` should explain the contents of the `Markdown/` folder, highlighting the `SOURCE_READY.md` file for LLM use and the `raw_chapters/` for granular reference.

## Acceptance Criteria for v0.1
1. One single consolidated `.md` file is generated per book.
2. The file contains valid YAML frontmatter.
3. The file contains a working internal Table of Contents.
4. Chapter boundaries are explicitly marked with HTML comments.
5. All code blocks and tables from the source are preserved.
6. Repeated boilerplate (e.g., "Download from O'Reilly") is removed.

## Out of Scope for v0.1
- Automated upload to ChatGPT.
- Image embedding (base64) in Markdown.
- Multi-book consolidation.
