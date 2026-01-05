# O'Reilly Downloader

Download books from O'Reilly Learning Platform and convert them to PDF, EPUB, plain text, or JSON.

## Disclaimer

This tool is for personal and educational purposes only. I am not responsible for how this program is used. Before using, please read the [O'Reilly Terms of Service](https://www.oreilly.com/terms/).

## Features

- Web interface for searching and downloading
- PDF, EPUB, plain text, and JSON output
- Downloads images and stylesheets

## Requirements

- Python 3.10+
- Active O'Reilly Learning subscription

## Installation

```bash
git clone https://github.com/yourusername/oreilly-downloader.git
cd oreilly-downloader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup Cookies

1. Go to [learning.oreilly.com](https://learning.oreilly.com) and log in
2. Open DevTools (F12)
3. Go to Application > Cookies > https://learning.oreilly.com
4. Create a `cookies.json` file in the project root with the following format:

```json
{
  "BrowserCookie": "your_browser_cookie_value",
  "OptanonConsent": "your_optanon_consent_value"
}
```

Copy the values from the DevTools cookies panel.

## Usage

```bash
python main.py
```

Open http://localhost:8000 in your browser.

### Options

```bash
python main.py --host 0.0.0.0 --port 9000
```

| Flag | Default | Description |
|------|---------|-------------|
| --host | localhost | Server host |
| --port | 8000 | Server port |

## Docker

### Quick Start

```bash
docker compose up
```

Open http://localhost:8000

### Build and Run Manually

```bash
docker build -t oreilly-downloader .
docker run -p 8000:8000 -v ./cookies.json:/app/cookies.json:ro -v ./output:/app/output oreilly-downloader
```

## Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| OUTPUT_DIR | ./output | Where books are saved |
| REQUEST_DELAY | 0.5 | Delay between requests (seconds) |
| REQUEST_TIMEOUT | 30 | Request timeout (seconds) |

## License

MIT
