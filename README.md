# O'Reilly Ingest

We're in the AI era. You want to chat with your favorite technical books and video courses using Claude Code, Cursor, or any LLM/RAG tool. This gets you there.

Export any O'Reilly book or video course to Markdown, Chunks (RAG), PDF, EPUB, JSON, TOON, or plain text. Download by chapters/lessons so you don't burn through your context window. For video courses, optionally download high-definition MP4 streams and synchronized WebVTT subtitles alongside structured Markdown transcripts.

> Requires a valid O'Reilly Learning subscription.

## Disclaimer

For personal and educational use only. Please read the [O'Reilly Terms of Service](https://www.oreilly.com/terms/).

## Credits

Inspired by [safaribooks](https://github.com/lorenzodifuccia/safaribooks) by [@lorenzodifuccia](https://github.com/lorenzodifuccia).


## Features

- **Books & Video Courses** - seamless support for both written books and full video courses
- **Syllabus & Hands-On Exercises** - generates course syllabus (`000_course_syllabus_and_exercises.md`) with module structure, exercise repo links, and quizzes
- **Timestamped Transcripts** - sentence-aligned transcripts with `[MM:SS - MM:SS]` timestamps per video lesson, ready for RAG citations
- **Multi-Format Video Exports** - choose between lightweight text transcripts (`Markdown`, `Chunks`, `JSON`) or direct video streams (`MP4 + VTT + MD`)
- **Export by chapters/lessons** - save tokens, focus on what matters
- **LLM-ready formats** - Markdown, Chunks, JSON, TOON, plain text optimized for AI
- **Publication Freshness & Sorting** - publication year badges (`📅 2025`) and search sorting (`Newest First`, `Relevance`, `Oldest First`)
- **Traditional formats** - PDF and EPUB 3
- **High-resolution covers** - print-quality 1200w book covers
- **O'Reilly V2 API** - fast and reliable with resilient retry backoff
- **Web UI** - search, preview, sort, and download

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

<img src="docs/cookie-modal.png" alt="Cookie Setup" style="max-width:320px; height:auto;">

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
