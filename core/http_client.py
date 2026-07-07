import base64
import contextlib
import json
import time
from pathlib import Path

from curl_cffi import requests

import config
from core.state.cookies import CookieHandler


class HttpClient:
    # Akamai bot-management cookies are tied to the original browser TLS session.
    # Sending them from a non-browser client causes Akamai to return 403.
    _AKAMAI_COOKIE_PREFIXES = ("_abck", "bm_", "ak_", "akaalb_")

    def __init__(self, cookies_file: Path | None = None):
        self._auth_cookies: dict = {}
        self.session = requests.Session(impersonate="safari17_0")
        self.session.headers.update(config.HEADERS)
        self.last_request_time = 0
        self.cookies_file = cookies_file or config.COOKIES_FILE

        if self.cookies_file.exists():
            self._load_cookies(self.cookies_file)

    def _load_cookies(self, path: Path):
        with contextlib.suppress(json.JSONDecodeError, ValueError):
            cookies = CookieHandler.load_cookies(path)
            if cookies:
                self._auth_cookies = {
                    k: v
                    for k, v in cookies.items()
                    if not k.startswith(self._AKAMAI_COOKIE_PREFIXES)
                }

    def _apply_auth_cookies(self):
        """Reset session to only auth cookies, discarding any Akamai cookies
        injected by previous responses."""
        self.session.cookies.clear()
        self.session.cookies.update(self._auth_cookies)

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
        self._apply_auth_cookies()
        return self.session.get(url, **kwargs)

    def get_json(self, url: str, **kwargs) -> dict:
        response = self.get(url, **kwargs)
        self._raise_for_auth_error(response)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str, **kwargs) -> str:
        response = self.get(url, **kwargs)
        self._raise_for_auth_error(response)
        response.raise_for_status()
        return response.text

    def get_bytes(self, url: str, **kwargs) -> bytes:
        response = self.get(url, **kwargs)
        self._raise_for_auth_error(response)
        response.raise_for_status()
        return response.content

    def _raise_for_auth_error(self, response) -> None:
        """Raise a descriptive RuntimeError on 4xx auth errors instead of raw HTTP errors."""
        if response.status_code == 403:
            if not self._auth_cookies:
                raise RuntimeError(
                    "Not authenticated. Please copy cookies from your browser and POST them to /api/cookies."
                )
            raise RuntimeError(
                "Session token expired. Please copy fresh cookies from your browser and POST them to /api/cookies."
            )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code} fetching {response.url}")

    @staticmethod
    def _decode_jwt_payload(token: str) -> dict | None:
        try:
            payload_b64 = token.split(".")[1]
            padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
            return json.loads(base64.b64decode(padded))
        except Exception:
            return None

    def get_jwt_status(self) -> dict | None:
        """Return JWT validity info without an HTTP round-trip.

        Returns None if no orm-jwt cookie is present.
        Returns dict with valid/reason/expires_at otherwise.
        """
        token = self._auth_cookies.get("orm-jwt")
        if not token:
            return None
        payload = self._decode_jwt_payload(token)
        if not payload:
            return {"valid": False, "reason": "invalid_token"}
        exp = payload.get("exp", 0)
        expires_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(exp))
        if time.time() > exp - 60:
            return {"valid": False, "reason": "token_expired", "expires_at": expires_at}
        return {"valid": True, "reason": None, "expires_at": expires_at}

    def _jwt_expired(self) -> bool:
        status = self.get_jwt_status()
        return status is not None and not status["valid"]

    def reload_cookies(self):
        """Clear and reload cookies from file. Used after browser login."""
        self._auth_cookies = {}
        self.session.cookies.clear()
        if self.cookies_file.exists():
            self._load_cookies(self.cookies_file)
