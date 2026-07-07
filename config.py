import os
from pathlib import Path

# Package base directory — for accessing package-internal resources only.
# Do NOT derive user data paths from this (would write into site-packages
# when installed via pip).
_BASE_DIR = Path(__file__).parent

# Output directory for downloaded books.
# Defaults to ./output (CWD-relative); override via OREILLY_OUTPUT_DIR.
OUTPUT_DIR = Path(os.environ.get("OREILLY_OUTPUT_DIR", "output"))

# State directory for runtime state (cookies, queue, etc.).
# Follows XDG_STATE_HOME convention; override via OREILLY_STATE_DIR.
_state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
STATE_DIR = Path(os.environ.get("OREILLY_STATE_DIR", _state_home / "oreilly-ingest"))

COOKIES_FILE = STATE_DIR / "cookies.json"
COOKIES_TXT_FILE = STATE_DIR / "cookies.txt"
QUEUE_FILE = STATE_DIR / "queue.json"

DATA_DIR = _BASE_DIR / "data"

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
    # User-Agent is intentionally omitted — curl_cffi sets it to match the
    # browser impersonation (safari17_0), and overriding it would cause a
    # TLS-fingerprint/UA mismatch that Akamai detects as a bot.
}
