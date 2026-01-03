import json
import time
from pathlib import Path

import requests

import config


class HttpClient:
    def __init__(self, cookies_file: Path | None = None):
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.last_request_time = 0

        cookies_path = cookies_file or config.COOKIES_FILE
        if cookies_path.exists():
            self._load_cookies(cookies_path)

    def _load_cookies(self, path: Path):
        try:
            with open(path) as f:
                cookies = json.load(f)
            if isinstance(cookies, dict):
                for name, value in cookies.items():
                    self.session.cookies.set(name, value, domain=".oreilly.com")
        except (json.JSONDecodeError, ValueError):
            pass  # Empty or invalid file, skip loading

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < config.REQUEST_DELAY:
            time.sleep(config.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        self._rate_limit()
        if not url.startswith("http"):
            url = config.BASE_URL + url
        kwargs.setdefault("timeout", config.REQUEST_TIMEOUT)
        return self.session.get(url, **kwargs)

    def get_json(self, url: str, **kwargs) -> dict:
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str, **kwargs) -> str:
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.text

    def get_bytes(self, url: str, **kwargs) -> bytes:
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.content

    def reload_cookies(self):
        """Clear and reload cookies from file. Used after browser login."""
        self.session.cookies.clear()
        if config.COOKIES_FILE.exists():
            self._load_cookies(config.COOKIES_FILE)
