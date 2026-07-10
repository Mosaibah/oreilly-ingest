import base64
import contextlib
import json
import time
from pathlib import Path

from curl_cffi import requests

import config


class HttpClient:
    # Akamai bot-management cookies (_abck, bm_*) must be sent: combined with the
    # safari17_0 TLS impersonation below, Akamai accepts the browser's _abck token
    # and returns 200. Stripping them causes Akamai to return 403 on protected
    # endpoints (e.g. /api/v2/epubs/), which surfaces as a spurious "auth" error.
    _AKAMAI_COOKIE_PREFIXES = ("_abck", "bm_", "ak_", "akaalb_")

    def __init__(self, cookies_file: Path | None = None):
        self._auth_cookies: dict = {}
        self.session = requests.Session(impersonate="safari17_0")
        self.session.headers.update(config.HEADERS)
        self.last_request_time = 0

        cookies_path = cookies_file or config.COOKIES_FILE
        if cookies_path.exists():
            self._load_cookies(cookies_path)

    def _load_cookies(self, path: Path):
        with contextlib.suppress(json.JSONDecodeError, ValueError):
            with open(path) as f:
                cookies = json.load(f)
            if isinstance(cookies, dict):
                # Keep all cookies, including the Akamai bot-management cookies
                # (_abck, bm_*) — they are required to pass Akamai (see class note).
                self._auth_cookies = dict(cookies)

    def _apply_auth_cookies(self):
        """Reset the session to the original browser cookies before each request.

        Replaying the known-good browser cookies (rather than the evolving set
        Akamai injects via Set-Cookie) keeps every request looking like the
        original browser session."""
        self.session.cookies.clear()
        self.session.cookies.update(self._auth_cookies)

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < config.REQUEST_DELAY:
            time.sleep(config.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        if not url.startswith("http"):
            url = config.BASE_URL + url
        kwargs.setdefault("timeout", config.REQUEST_TIMEOUT)

        last_exc = None
        for attempt in range(config.MAX_RETRIES):
            self._rate_limit()
            self._apply_auth_cookies()
            try:
                return self.session.get(url, **kwargs)
            except Exception as e:  # curl_cffi raises on timeout/connection errors
                last_exc = e
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BACKOFF * (attempt + 1))
        raise last_exc

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
            # A 403 has two distinct causes. Only call it "expired" when the JWT
            # actually is; otherwise it is Akamai bot-blocking the request, and
            # telling the user to refresh the *token* is misleading.
            if self._jwt_expired():
                raise RuntimeError(
                    "Session token expired. Please copy fresh cookies from your browser and POST them to /api/cookies."
                )
            raise RuntimeError(
                "Blocked by O'Reilly bot protection (Akamai 403) even though the session "
                "token is still valid. Copy fresh cookies from your browser — including the "
                "_abck and bm_* cookies — and POST them to /api/cookies."
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"HTTP {response.status_code} fetching {response.url}"
            )

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
        if config.COOKIES_FILE.exists():
            self._load_cookies(config.COOKIES_FILE)
