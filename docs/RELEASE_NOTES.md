# Release Notes

## v0.1-combiner (2026-05-22)
- Implemented standalone post-export combiner: `utils/source_ready_combiner.py`.
- Generates `<Book_Title>__SOURCE_READY.md` optimized for LLM ingestion.
- Generates `source_ready_manifest.json` with detailed indexing.
- Key features:
  - Valid YAML frontmatter with book metadata.
  - Source Usage Notes and detailed Book Metadata sections.
  - Internal Table of Contents with stable anchors.
  - Machine-parseable `CHAPTER_START` and `CHAPTER_END` markers.
  - Manifest consistency: distinguishes between source links, included chapters, and missing chapters.
- Verification:
  - Passed `py_compile`.
  - Successfully processed `soccer-analytics-with-machine-learning`:
    - 15 chapters included.
    - 2 missing chapters (`cover.md`, `copyright-page01.md`) correctly reported.
- Limitations:
  - Chapter order depends on `README.md` structure.
  - Missing chapter files are skipped with warnings.
  - Generated output in `output/` is ignored by git.

## v0.1-shaping (2026-05-22)
- Created initial governance and project-shaping documentation.
- Defined "Source-Ready" consolidated Markdown format.
- Established non-negotiable AI agent rules.
- Mapped implementation backlog.

## v0.1-target (Planned)
- First implementation of consolidated Markdown export.
- YAML frontmatter inclusion.
- Internal Table of Contents generation.
- Chapter boundary marking.
- `raw_chapters/` organization.

## Known Risks
- **BOILERPLATE:** Some books have heavy navigation/legal text in every chapter. Cleanup might be needed in `html_processor.py`.
- **ANCHORS:** If `markdownify` strips certain ID attributes, internal links in the TOC might break.

## Definition of Done
A slice is "Done" when:
- Implementation is complete.
- All tests in `TEST_PLAN.md` pass.
- Code is reviewed by the user.
- Documentation is updated.
- It is merged into the branch.
