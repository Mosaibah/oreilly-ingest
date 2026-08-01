# Task Backlog

## Slice 0: Project Shaping & Governance
- **Objective:** Establish the roadmap and rules.
- **Allowed Files:** `/docs/*`
- **Forbidden Files:** All others.
- **Acceptance Criteria:** All shaping docs created and aligned with product intent.
- **Status:** DONE

## Slice 1: Consolidated Source-Ready Export
- **Objective:** Create a post-export combiner script to produce the single-file output.
- **Allowed Files:** `utils/source_ready_combiner.py` (new)
- **Forbidden Files:** `core/*`, `web/*`, `plugins/markdown.py` (unless explicitly approved)
- **Acceptance Criteria:** `<Book_Title>__SOURCE_READY.md` generated with YAML and TOC by reading an existing export folder.
- **Verification:** Verified on `soccer-analytics-with-machine-learning`. 15 chapters included, manifest generated, py_compile passed.
- **Status:** DONE

## Slice 2: Manifest & Reporting Hardening
- **Objective:** Ensure `manifest.json` and `README.md` are comprehensive.
- **Allowed Files:** `plugins/markdown.py`
- **Acceptance Criteria:** Manifest contains all required fields for automated ingestion tools.
- **Status:** BACKLOG

## Slice 3: Markdown Cleanup Rules
- **Objective:** Strip boilerplate, fix broken links, and optimize for LLM token usage.
- **Allowed Files:** `plugins/markdown.py`, `plugins/html_processor.py`
- **Acceptance Criteria:** Reduced noise in consolidated file; no "Download our app" text.
- **Status:** BACKLOG

## Slice 4: Manual Audit Workflow
- **Objective:** Create a script/process for a human to verify export quality.
- **Allowed Files:** `utils/audit.py` (new)
- **Status:** BACKLOG

## Slice 5: Optional Docling Fallback
- **Objective:** Integrate Docling for PDF-only book sources.
- **Allowed Files:** `plugins/pdf.py` (or new plugin)
- **Status:** BACKLOG
