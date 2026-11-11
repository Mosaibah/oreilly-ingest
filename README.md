# O'Reilly Ingest

We're in the AI era. You want to chat with your favorite technical books using Claude Code, Cursor, or any LLM tool. This gets you there.

Export any O'Reilly book to Markdown, PDF, EPUB, JSON, TOON, or plain text. Download by chapters so you don't burn through your context window.

> Requires a valid O'Reilly Learning subscription.

## Disclaimer

For personal and educational use only. Please read the [O'Reilly Terms of Service](https://www.oreilly.com/terms/).

## Credits

Inspired by [safaribooks](https://github.com/lorenzodifuccia/safaribooks) by [@lorenzodifuccia](https://github.com/lorenzodifuccia).


## Features

- **Export by chapters** - save tokens, focus on what matters
- **LLM-ready formats** - Markdown, JSON, TOON, plain text optimized for AI
- **Traditional formats** - PDF and EPUB 3
- **O'Reilly V2 API** - fast and reliable
- **Images & styles included** - complete book experience
- **Non-English editions** - search with a language filter (English, Japanese/日本語, …), paste a translated book's URL or ISBN, and see other-language editions on the book card
- **Web UI** - search, preview, download

<img src="docs/main.png" alt="Main Page">

## Non-English (translated) books

O'Reilly hosts translated editions (Japanese, Chinese, …) as separate books
with their own ISBNs. Two platform limitations shaped this app's behaviour:

- **Keyword search cannot match translated titles.** The search index does not
  tokenize Japanese/Chinese metadata — searching `ドメイン駆動設計をはじめよう` returns
  nothing. To open a translated book, **paste its URL**, **search by ISBN**
  (the app automatically probes each language's index, so a translated ISBN
  resolves), or use the **Language** filter next to the search box to browse
  that language directly.
- **Each language is a separate book entry.** An expanded card shows a
  `Language` line plus *Other language editions* (e.g. the Japanese version of
  an English title) that you can open and download directly.

Output declares the book's own language (`dc:language` for EPUB, `lang` for
PDF), and PDF generation falls back to CJK system fonts so Japanese ebooks do
not render as tofu.

## Quick Start

### Docker

```bash
git clone https://github.com/mosaibah/oreilly-downloader.git
cd oreilly-downloader
docker compose up -d
```

### Python

```bash
git clone https://github.com/mosaibah/oreilly-downloader.git
cd oreilly-downloader
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Then open http://localhost:8000

## Setting Up Cookies

Click "Set Cookies" in the web interface and follow the steps:

<img src="docs/cookie-modal.png" alt="Cookie Setup" style="max-width:320px; height:auto;">

The `orm-jwt` session token is **short-lived (~15 minutes)**, so cookies copied
by hand go stale almost immediately. Search requires a fresh token, but
**downloads continue to work with an expired token** (metadata, chapters and
content are served by public V2 epub endpoints). To re-sync cookies
automatically from Chrome:

```bash
pip install pycookiecheat
python scripts/refresh_cookies.py --watch   # re-sync every 60s
```

## Architecture

Plugin-based microkernel design:

| Layer | Components |
|-------|------------|
| **Kernel** | Plugin registry, shared HTTP client |
| **Core** | Auth, Book, Chapters, Assets, HtmlProcessor |
| **Output** | Epub, Markdown, Pdf, PlainText, JsonExport, ToonExport |
| **Utility** | Chunking, Token, Downloader |

### API

```
GET  /api/status                  - auth check
GET  /api/search?q=&language=     - find books (language filter: en, ja, zh, …)
GET  /api/book/{id}               - metadata
GET  /api/book/{id}/translations  - editions in other languages
GET  /api/book/{id}/chapters      - chapter list for the chapter picker
POST /api/download                - start export
GET  /api/progress                - SSE stream
```

## Testing

```bash
python -m unittest discover tests            # run all unit tests
python -m unittest tests/test_book_search.py  # offline: normalization + language probe logic
python -m unittest tests/test_ja_download.py  # network: full pipeline on the Japanese edition
```

## Contributing

Found a bug or have an idea? PRs and issues are always welcome!


## Recent Changes

- **Chunking: streaming & memory fix** — `chunk_book()` now streams chunks directly to disk instead of accumulating in memory. Replaced `tiktoken` tokenizer with a word-count heuristic to avoid memory spikes on large books. (@zirkleta)
- **System: command injection fix** — `_show_macos_picker()` rejects paths containing `"` before interpolating into osascript, preventing command injection via crafted directory names. (@zirkleta)
- **`patch_chunk_titles.py`** — New utility script that backfills `book_title` into existing `*_chunks.jsonl` files in the output directory. (@zirkleta)

## License

MIT

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
