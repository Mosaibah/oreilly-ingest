# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

O'Reilly Learning Platform book downloader using a microkernel architecture. Downloads books and converts them to PDF, EPUB, Markdown, plain text, or JSON format. Python 3.10+, vanilla Python with minimal dependencies.

## Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the web server
python main.py                    # Default: localhost:8000
python main.py --port 9000        # Custom port

# Run with venv directly
.venv/bin/python main.py
```

## Architecture

### Microkernel Pattern
- **Kernel** (`core/kernel.py`): Plugin registry, provides shared `HttpClient` to all plugins
- **Plugins** (`plugins/`): Independent modules registered with the kernel, access HTTP via `self.http`
- Plugins extend `Plugin` base class from `plugins/base.py`
- Use `create_default_kernel()` to get a fully configured kernel with all plugins

### Plugin Categories

**Core Plugins** (data acquisition):
- `AuthPlugin` - Session validation via /profile/
- `BookPlugin` - Fetch metadata (V2 Search + V2 Epubs APIs)
- `ChaptersPlugin` - Fetch chapter list and content
- `AssetsPlugin` - Download CSS and images
- `HtmlProcessorPlugin` - Extract sbo-rt-content, rewrite links, wrap XHTML

**Output Format Plugins**:
- `EpubPlugin` - Generate EPUB structure and ZIP
- `MarkdownPlugin` - Convert HTML to Markdown
- `PdfPlugin` - Generate PDF output
- `PlainTextPlugin` - Extract plain text
- `JsonExportPlugin` - Export structured JSON
- `ChunkingPlugin` - Split content into chunks
- `TokenPlugin` - Token counting

**Orchestration Plugins**:
- `OutputPlugin` - Coordinate output generation
- `SystemPlugin` - System information
- `DownloaderPlugin` - Orchestrate full download workflow

### Web Server
- `web/server.py`: HTTP server using `http.server`, serves static files from `web/static/`
- JSON API endpoints: `/api/status`, `/api/search`, `/api/book/{id}`, `/api/download`, `/api/progress`

### Key Files
- `config.py`: BASE_URL, API_V1, API_V2, OUTPUT_DIR, COOKIES_FILE, REQUEST_DELAY
- `cookies.json`: User-provided O'Reilly session cookies (BrowserCookie, OptanonConsent)
- `output/`: Downloaded books stored here as `{book_title}/` directories

## API Strategy

Use V2 APIs primarily:
- **V2 Search** (`/api/v2/search/?query={ISBN}`) - authors, publishers, topics, cover_url
- **V2 Epubs** (`/api/v2/epubs/urn:orm:book:{ID}/`) - spine, chapters URL, TOC URL
- **V2 Chapters** (`/api/v2/epub-chapters/`) - full chapter metadata with `related_assets`
- **V2 Content** returns `sbo-rt-content` div directly (no full HTML parsing needed)

## Content Pipeline

1. Fetch book metadata (BookPlugin)
2. Fetch chapters list with pagination (ChaptersPlugin)
3. For each chapter: fetch HTML, extract `sbo-rt-content`, collect CSS/images
4. Rewrite links (.html → .xhtml, image paths → Images/)
5. Download all CSS and images (AssetsPlugin)
6. Generate output format: EPUB, PDF, Markdown, plain text, or JSON

## Adding a New Plugin

```python
from plugins.base import Plugin

class NewPlugin(Plugin):
    def do_something(self, params):
        # Access HTTP client via self.http
        response = self.http.get(url)
        # Access other plugins via self.kernel["plugin_name"]
        return result
```

Register in `core/kernel.py`:
```python
kernel.register("new_plugin", NewPlugin())
```

## Reference Documentation

- `TECHNICAL_DOCUMENTATION.md` - Complete V1 API specification, EPUB generation details
- `API_V2_DOCUMENTATION.md` - V2 API endpoints with differences from V1
