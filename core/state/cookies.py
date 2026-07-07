"""Cookie loading and saving for the shared core state directory."""

import json
from pathlib import Path

import config


class CookieHandler:
    """Load and parse cookies from JSON or Netscape Cookie File formats."""

    @staticmethod
    def load_cookies(cookie_path: Path | None = None) -> dict:
        """
        Load cookies from file (JSON or Netscape format).

        Args:
            cookie_path: Path to cookies file. If None, tries default locations.

        Returns:
            Dictionary of cookies.
        """
        if cookie_path is None:
            paths_to_try = [
                config.COOKIES_FILE,
                config.COOKIES_TXT_FILE,
                config.BASE_DIR / "cookies.json",
                config.BASE_DIR / "cookies.txt",
                config.DATA_DIR / "cookies.json",
                config.DATA_DIR / "cookies.txt",
            ]

            for path in paths_to_try:
                if path.exists():
                    cookie_path = path
                    break

            if cookie_path is None:
                return {}

        if not cookie_path.exists():
            return {}

        if cookie_path.suffix == ".json":
            return CookieHandler._load_json_cookies(cookie_path)
        if cookie_path.suffix == ".txt":
            return CookieHandler._load_netscape_cookies(cookie_path)

        try:
            return CookieHandler._load_json_cookies(cookie_path)
        except (json.JSONDecodeError, ValueError):
            return CookieHandler._load_netscape_cookies(cookie_path)

    @staticmethod
    def save_json_cookies(cookies: dict, cookie_path: Path | None = None) -> Path:
        """Persist cookies to the shared JSON cookie file."""
        cookie_path = cookie_path or config.COOKIES_FILE
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_path.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        return cookie_path

    @staticmethod
    def _load_json_cookies(path: Path) -> dict:
        """Load cookies from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data
        raise ValueError("JSON cookies must be a dictionary")

    @staticmethod
    def _load_netscape_cookies(path: Path) -> dict:
        """
        Load cookies from Netscape HTTP Cookie File format.

        Format:
        # domain    flag    path    secure    expiration    name    value
        .oreilly.com    TRUE    /    FALSE    0    cookie_name    cookie_value
        """
        cookies = {}

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) >= 7:
                    name = parts[5]
                    value = parts[6]
                    cookies[name] = value

        return cookies
