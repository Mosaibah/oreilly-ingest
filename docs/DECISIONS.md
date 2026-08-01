# Decision Log

## D-001: Prefer Native Export
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Books are available in HTML/XHTML via the O'Reilly API.
- **Decision:** Always prefer native Markdown conversion over PDF-to-Markdown to preserve semantic structure.
- **Consequences:** Cleaner output, lower token noise, less reliance on OCR.

## D-002: Single Consolidated File as Primary Artifact
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** ChatGPT Projects have limited upload slots.
- **Decision:** The primary output of the Markdown pipeline must be one single `<Book_Title>__SOURCE_READY.md` file.
- **Consequences:** Easier management for users; better context for LLM if internal anchors are correct.

## D-003: Preserve Per-Chapter Files
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Granular files are useful for debugging or targeted reference.
- **Decision:** Keep per-chapter `.md` files in a `raw_chapters/` subdirectory.
- **Consequences:** No loss of existing functionality; better flexibility.

## D-004: Docling as PDF Fallback
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Some sources are PDF-only.
- **Decision:** Use Docling only when native HTML/EPUB sources are unavailable.
- **Consequences:** Higher quality defaults with a robust fallback.

## D-005: No Coding Before Shaping
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Prevent scope creep and architecture drift.
- **Decision:** All implementation must be preceded by approved docs in `/docs`.
- **Consequences:** Slower start, but higher quality and predictable outcomes.

## D-006: Bounded Agent Tasks
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** LLM agents can over-reach.
- **Decision:** Agents execute specific slices; they do not redefine product direction.
- **Consequences:** User maintains control over architecture and strategy.

## D-007: Localization to MarkdownPlugin
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Audit shows most logic resides in `plugins/markdown.py`.
- **Decision:** Target the next slice exclusively at the Markdown plugin layer.
- **Consequences:** Minimizes risk to core kernel and other output formats.

## D-008: Post-Export Combiner Approach for v0.1
- **Date:** 2026-05-22
- **Status:** Approved
- **Context:** Modifying the existing `MarkdownPlugin` risks breaking existing user workflows and changing established output patterns.
- **Decision:** Implement the consolidated Source-ready Markdown generation as a separate post-export combiner script (`utils/source_ready_combiner.py`).
- **Consequences:** Existing behavior is preserved; new functionality is isolated; easier to test and iterate without affecting the core download engine.
