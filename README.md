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

1. Open [learning.oreilly.com](https://learning.oreilly.com) and log in.
2. Open the browser console (`F12` → Console).
3. Paste the following command and press Enter:

```js
Object.fromEntries(document.cookie.split(';').map(c => c.split('=').map(s => s.trim())))
```

4. Copy the output and paste it into the cookie field.

<img src="docs/cookie-modal.png" alt="Cookie Setup" style="max-width:320px; height:auto;">

## Architecture

Plugin-based microkernel design:

| Layer | Components |
|-------|------------|
| **Kernel** | Plugin registry, shared HTTP client |
| **Core** | Auth, Book, Chapters, Assets, HtmlProcessor |
| **Output** | Epub, Markdown, Pdf, PlainText, JsonExport |
| **Utility** | Chunking, Token, Downloader |

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
