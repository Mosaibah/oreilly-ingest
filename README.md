# O'Reilly Ingest

We're in the AI era. You want to chat with your favorite technical books using Claude Code, Cursor, or any LLM tool. This gets you there.

Export any O'Reilly book to Markdown, PDF, EPUB, JSON, or plain text. Download by chapters so you don't burn through your context window.

> Requires a valid O'Reilly Learning subscription.

## Disclaimer

For personal and educational use only. Please read the [O'Reilly Terms of Service](https://www.oreilly.com/terms/).

## Credits

Inspired by [safaribooks](https://github.com/lorenzodifuccia/safaribooks) by [@lorenzodifuccia](https://github.com/lorenzodifuccia).

## Features

- **Export by chapters** - save tokens, focus on what matters
- **LLM-ready formats** - Markdown, JSON, plain text optimized for AI
- **Traditional formats** - PDF and EPUB 3
- **O'Reilly V2 API** - fast and reliable
- **Images & styles included** - complete book experience
- **Web UI** - search, preview, download

<img src="docs/main.png" alt="Main Page">

## Quick Start

### Docker

```bash
git clone https://github.com/mosaibah/oreilly-ingest.git
cd oreilly-ingest
docker compose up -d
```

### pip (CLI)

```bash
pip install git+https://github.com/mosaibah/oreilly-ingest.git
oreilly-ingest
```

Or from a local checkout:

````bash
git clone https://github.com/mosaibah/oreilly-ingest.git
cd oreilly-ingest
pip install .
oreilly-ingest

### Python (venv)

```bash
git clone https://github.com/mosaibah/oreilly-ingest.git
cd oreilly-ingest
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
````

Then open http://localhost:8000

## Setting Up Cookies

Place your exported O'Reilly session cookies in `core/state/` using either filename:

- `core/state/cookies.json` — JSON format
- `core/state/cookies.txt` — Netscape HTTP Cookie File format

To export cookies from your browser:

1. Open the O'Reilly Learning Platform.
2. Open Developer Tools (`F12`).
3. Go to **Application** → **Cookies** → `learning.oreilly.com`.
4. Export the cookies as JSON or Netscape format.

Alternatively, on the web interface, click "Set Cookies" and follow the steps.

## CLI Usage

### Web Server

```bash
oreilly-ingest                 # defaults to localhost:8000
oreilly-ingest --port 9000     # custom port
```

Or with the venv approach:

```bash
python main.py                 # defaults to localhost:8000
python main.py --port 9000     # custom port
```

### Download Commands

```bash
# Download a book as EPUB
oreilly-ingest download 0123456789
python main.py download 0123456789

# Download as Markdown with separate files per chapter
oreilly-ingest download 0123456789 --format markdown --separate

# Download multiple formats
oreilly-ingest download 0123456789 --format "markdown,pdf,json"

# Download specific chapters only
oreilly-ingest download 0123456789 --format markdown --chapters selected --chapter-list "1,2,3"
```

### Queue Management

```bash
oreilly-ingest queue add 0111111111 --format epub
oreilly-ingest queue add 0222222222 --format "markdown,pdf"
oreilly-ingest queue process
oreilly-ingest queue list
oreilly-ingest queue remove abc12345
```

### Check Config

```bash
oreilly-ingest config
```

### Export Formats

| Format     | Aliases            | Notes                                                              |
| ---------- | ------------------ | ------------------------------------------------------------------ |
| EPUB       | `epub`             | Default format; available for full-book exports only               |
| Markdown   | `markdown`, `md`   | Per-chapter files only                                             |
| JSON       | `json`             | Structured export; supports combined or separate chapter files    |
| Plain text | `plaintext`, `txt` | Supports combined or separate chapter files                        |
| PDF        | `pdf`              | Supports combined or separate chapter files (`pdf-chapters`)       |
| Chunks     | `chunks`           | LLM-oriented chunked content; available for full-book exports only |

### Chapter Selection

```bash
# Download every chapter (default)
oreilly-ingest download 0123456789 --chapters all

# Download selected chapters
oreilly-ingest download 0123456789 \
  --chapters selected \
  --chapter-list "1,2,3"
```

### Output Modes

For Markdown, JSON, plain-text, and PDF exports:

```bash
# Create one combined output file (default)
oreilly-ingest download 0123456789 --format markdown --combined

# Create one output file per chapter
oreilly-ingest download 0123456789 --format markdown --separate
```

## Architecture

Plugin-based microkernel design:

| Layer       | Components                                                               |
| ----------- | ------------------------------------------------------------------------ |
| **Kernel**  | Plugin registry, shared HTTP client                                      |
| **Core**    | Auth, Book, Chapters, Assets, HtmlProcessor, CookieHandler, QueueHandler |
| **Output**  | Epub, Markdown, Pdf, PlainText, JsonExport                               |
| **Utility** | Chunking, Token, Downloader                                              |

### API

```
GET  /api/status       - auth check
GET  /api/search?q=    - find books
GET  /api/book/{id}    - metadata
POST /api/download     - start export
GET  /api/progress     - SSE stream
```

## Contributing

Found a bug or have an idea? PRs and issues are always welcome!

## Recent Changes

- **Chunking: streaming & memory fix** — `chunk_book()` now streams chunks directly to disk instead of accumulating in memory. Replaced `tiktoken` tokenizer with a word-count heuristic to avoid memory spikes on large books. (@zirkleta)
- **System: command injection fix** — `_show_macos_picker()` rejects paths containing `"` before interpolating into osascript, preventing command injection via crafted directory names. (@zirkleta)
- **`patch_chunk_titles.py`** — New utility script that backfills `book_title` into existing `*_chunks.jsonl` files in the output directory. (@zirkleta)

## License

[MIT](LICENSE)

## Star History

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="
      https://api.star-history.com/svg?repos=Mosaibah/oreilly-ingest&type=Date&theme=dark
    "
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="
      https://api.star-history.com/svg?repos=Mosaibah/oreilly-ingest&type=Date
    "
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=Mosaibah/oreilly-ingest&type=Date"
  />
</picture>
