# Architecture: Markdown Export Pipeline

## Current Architecture (Audit Findings)
The application uses a microkernel architecture where functionality is encapsulated in plugins registered with a central `Kernel`.

- **Kernel (`core/kernel.py`):** Manages plugin registration and access.
- **Downloader (`plugins/downloader.py`):** Orchestrates the high-level workflow (metadata -> chapters -> assets -> formats).
- **MarkdownPlugin (`plugins/markdown.py`):** Handles the specific conversion from HTML to Markdown.
- **HTML Processor (`plugins/html_processor.py`):** Cleans and prepares HTML before it reaches the Markdown stage.

## Expected Flow
1. **Source (`downloader.py`):** Fetches book metadata and chapter HTML/XHTML.
2. **Conversion (`markdown.py`):**
   - Calls `markdownify` for each chapter.
   - Cleans whitespace and fixes image paths.
3. **Storage (`markdown.py`):**
   - Saves individual chapters to the `Markdown/` folder.
   - Writes `README.md` with chapter links.
4. **Aggregation (Step 6 - Optional/Post-Processing):**
   - A separate combiner (`utils/source_ready_combiner.py`) reads the `Markdown/` folder.
   - Prepends YAML frontmatter and Table of Contents.
   - Wraps each chapter in markers.
   - Writes the final `SOURCE_READY.md`.
5. **Metadata:** Generates `source_ready_manifest.json`.

## Responsibility Boundaries
- **App/Exporter:** Registry and API management.
- **MarkdownPlugin:** Responsible for individual chapter conversion and `README.md`.
- **SourceReadyCombiner:** Primary owner of the consolidated format logic; acts as a post-processor.
- **HTML Processor:** Handles structural cleanup (e.g., removing `<nav>`, fixing `<img>` tags).
- **Future Docling:** Will act as a peer to `MarkdownPlugin` or a pre-processor for PDF sources.

## Architecture Constraints
- **Minimal Dependencies:** Use standard library (json, re) for frontmatter/manifest where possible.
- **Surgical Changes:** Modify only the Markdown layer unless the interface must change.
- **No Global State:** Plugins must rely on `book_info` and `chapters` data passed during invocation.

## Governance Rule
**Agents may not change the architecture (e.g., adding new core plugins or changing the Kernel interface) without explicit approval from the project lead.**
