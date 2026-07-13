#!/usr/bin/env python3
"""Refresh O'Reilly session cookies from the local Chrome profile.

O'Reilly's ``orm-jwt`` access token is short-lived (~15 minutes), so a cookie
snapshot copied by hand goes stale almost immediately. This helper reads the
current cookies straight from Chrome's cookie store and pushes them to the
running ingest app, so you never have to copy/paste them again.

Usage:
    python scripts/refresh_cookies.py                 # read Chrome + update app once
    python scripts/refresh_cookies.py --port 8000
    python scripts/refresh_cookies.py --no-post       # only write cookies.json
    python scripts/refresh_cookies.py --watch         # re-sync every 60s (Ctrl-C to stop)
    python scripts/refresh_cookies.py --watch 30      # re-sync every 30s

Reading Chrome cookies on macOS requires the browser's Keychain key; the first
run shows a one-time "Chrome Safe Storage" permission prompt — click Allow.

Cookie values are never printed.
"""

import argparse
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

from pycookiecheat import chrome_cookies

ORME_URL = "https://learning.oreilly.com/"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOT_COOKIES = Path(__file__).resolve().parent.parent / "cookies.json"


def _jwt_seconds_left(token: str) -> int | None:
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(payload.get("exp", 0) - time.time())
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh O'Reilly cookies from Chrome")
    parser.add_argument("--port", type=int, default=8000, help="Running app port")
    parser.add_argument("--host", default="localhost", help="Running app host")
    parser.add_argument("--no-post", action="store_true", help="Only write cookies.json, do not reload the app")
    parser.add_argument(
        "--watch", type=int, metavar="SECONDS", nargs="?", const=60, default=None,
        help="Keep running, re-syncing cookies every SECONDS (default 60) so long "
             "downloads stay authenticated. Ctrl-C to stop.",
    )
    args = parser.parse_args()

    # Stream output even when redirected/piped (important for --watch, whose
    # progress would otherwise be swallowed by stdout block-buffering).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

    if args.watch is None:
        return refresh_once(args)

    interval = max(5, args.watch)
    print(f"Watching Chrome cookies, re-syncing every {interval}s. Press Ctrl-C to stop.")
    print("Tip: click 'Always Allow' on the Keychain prompt so each re-sync "
          "doesn't block waiting for it.")
    try:
        while True:
            refresh_once(args)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


def refresh_once(args) -> int:
    """Read cookies from Chrome, write them to the app's cookies file, and reload
    the running app. Returns 0 on success, 1 on a fatal read error."""
    try:
        cookies = chrome_cookies(ORME_URL)
    except Exception as e:  # noqa: BLE001 - surface any Keychain/DB error clearly
        print(f"ERROR: could not read Chrome cookies: {e}", file=sys.stderr)
        print("Make sure Chrome is installed and you approved the Keychain prompt.", file=sys.stderr)
        return 1

    jwt = cookies.get("orm-jwt")
    if not jwt:
        print("ERROR: no 'orm-jwt' cookie found for learning.oreilly.com.", file=sys.stderr)
        print("Log in to O'Reilly in Chrome (Default profile), then retry.", file=sys.stderr)
        return 1

    left = _jwt_seconds_left(jwt)
    if left is not None and left <= 0:
        print(f"WARNING: the orm-jwt in Chrome is already expired ({left}s). "
              "Open learning.oreilly.com in Chrome to refresh it, then retry.", file=sys.stderr)

    # Write to whichever cookies file the app uses (data/ in Docker, root otherwise).
    target = (DATA_DIR / "cookies.json") if DATA_DIR.exists() else ROOT_COOKIES
    target.write_text(json.dumps(cookies, indent=2))
    print(f"Wrote {len(cookies)} cookies to {target}")
    if left is not None:
        print(f"orm-jwt valid for ~{left // 60}m {left % 60}s")

    if args.no_post:
        return 0

    # Reload the running app's in-memory session (host->host plain HTTP, no CORS issues).
    url = f"http://{args.host}:{args.port}/api/cookies"
    req = urllib.request.Request(
        url, data=json.dumps(cookies).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
        if body.get("success"):
            print(f"App reloaded cookies OK ({url})")
        else:
            print(f"App responded: {body}")
    except Exception as e:  # noqa: BLE001
        print(f"NOTE: wrote cookies.json but could not reach the app at {url}: {e}")
        print("Is the server running? Cookies file is updated regardless.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
