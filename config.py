from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Use data/ directory if it exists (Docker), otherwise use root (local dev)
DATA_DIR = BASE_DIR / "data"
if DATA_DIR.exists():
    COOKIES_FILE = DATA_DIR / "cookies.json"
else:
    COOKIES_FILE = BASE_DIR / "cookies.json"

BASE_URL = "https://learning.oreilly.com"
API_V1 = f"{BASE_URL}/api/v1"
API_V2 = f"{BASE_URL}/api/v2"

REQUEST_DELAY = 0.5
REQUEST_TIMEOUT = 30

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": BASE_URL,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
