# Release Notes

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
