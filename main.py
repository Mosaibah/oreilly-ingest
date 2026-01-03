#!/usr/bin/env python3
"""O'Reilly Downloader - Main Entry Point"""

import argparse
from web.server import run_server


def main():
    parser = argparse.ArgumentParser(description="O'Reilly Book Downloader")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    print("=" * 50)
    print("  O'Reilly Downloader")
    print("=" * 50)
    print(f"\n  Open http://{args.host}:{args.port} in your browser\n")
    print("  Press Ctrl+C to stop\n")
    print("=" * 50)

    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
