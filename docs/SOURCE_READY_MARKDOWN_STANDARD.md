# Source-Ready Markdown Standard

## 1. Goal
The goal of this standard is to ensure that every book exported by the O'Reilly Ingest pipeline is "Source-Ready" for ingestion into a ChatGPT Project or similar LLM context. This format optimizes for retrieval, context grounding, and structural clarity.

## 2. File Naming and Location
- The primary output file must be named: `<Book_Title>__SOURCE_READY.md`.
- It must reside in the `Markdown/` folder of the book's output directory.
- A `source_ready_manifest.json` must be present in the same directory.

## 3. Consolidated File Structure

### 3.1 YAML Frontmatter
The file must begin with a YAML block containing metadata for LLM ingestion:

```yaml
---
source: "<book title>"
author: "<authors>"
document_type: "book"
category: "<category>"
priority: "<Core | Supporting | Reference>"
use_for:
  - "retrieval inside ChatGPT Projects"
  - "chapter-level source grounding inside one consolidated file"
do_not_use_for:
  - "current real-time information"
  - "legal, medical, financial, or safety-critical advice unless independently verified"
processed_date: "YYYY-MM-DD"
pipeline_version: "native-md-export-v0.1"
conversion_profile: "native_markdown_export"
ocr_used: false
notes: "Generated directly from app HTML/XHTML export; consolidated and cleaned for LLM ingestion."
---
```

### 3.2 Header and Usage Notes
- `# <Book Title>`
- `## Source Usage Notes`
  - Explains when to use/not use this source.

### 3.3 Internal Table of Contents
- `## Book Table of Contents`
- A list of Markdown links to internal chapter anchors:
  - `[Chapter 1: ...](#chapter-1-...)`
  - `[Chapter 2: ...](#chapter-2-...)`

## 4. Chapter Formatting
Chapters must be wrapped in machine-parseable HTML comments.

```markdown
---

<!-- CHAPTER_START index="1" title="..." original_filename="..." -->

# Chapter 1. <Chapter Title>

<chapter content>

<!-- CHAPTER_END index="1" -->

---
```

## 5. Quality Requirements
- **Heading Style:** Use ATX-style headings (`#`, `##`, etc.).
- **Code Blocks:** Use triple backticks with language identifiers.
- **Tables:** Preserve structural integrity using Markdown table syntax.
- **Whitespace:** Collapse 3+ newlines into 2.
- **Cleanup:** 
  - Remove navigation boilerplate (Previous/Next/Table of Contents buttons).
  - Remove publisher/subscription boilerplate.
  - Preserve useful captions, definitions, and checklists.
- **Links:** Rewritten for internal consistency within the consolidated file or to reference `Images/`.
