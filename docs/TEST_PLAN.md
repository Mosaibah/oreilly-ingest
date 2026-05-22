# Test Plan

## Quality Gates

### 1. Slice 0: Documentation
- All files in `/docs` exist.
- Non-negotiable rules are explicitly stated.
- Tasks are clearly defined.

### 2. Slice 1: Consolidated Export (Combiner)
- **Syntax Check:** `python -m py_compile utils/source_ready_combiner.py` must pass.
- **Combiner Execution Check:** Running the script against an existing `Markdown/` folder must produce new files.
- **Consolidated File Checks:**
  - File name matches `<Book_Title>__SOURCE_READY.md`.
  - Starts with `---` (YAML frontmatter).
  - Contains `# Book Title` header.
  - Contains `## Source Usage Notes`.
  - Contains `## Book Table of Contents` with working links.
  - Every chapter is wrapped in `<!-- CHAPTER_START ... -->` and `<!-- CHAPTER_END -->`.
  - Chapter order matches the sequence in `README.md`.
- **Manifest Check:** `source_ready_manifest.json` contains metadata and chapter file mapping.

### 3. Regression Checks
- PDF export still works.
- EPUB export still works.
- Per-chapter Markdown files are still valid and readable.

## Manual Verification
- Open the consolidated `.md` in a Markdown viewer (or VS Code).
- Click TOC links to verify internal navigation.
- Search for "Chapter 1" to verify boundary markers.

## Stop Conditions
- Any change that breaks the `Kernel` registration.
- Any change that introduces a new dependency without approval.
- More than two failed attempts to fix a single bug.
