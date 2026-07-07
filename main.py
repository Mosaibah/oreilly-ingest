#!/usr/bin/env python3
"""O'Reilly Downloader - Main Entry Point (Web Server or CLI)"""

import argparse
import sys

from web.server import run_server
from cli.main import CLIApp


def _is_cli_mode(args: list[str]) -> bool:
    """
    Detect if the user is trying to run CLI commands.
    Returns True if args look like CLI commands (download, queue, etc).
    """
    if not args:
        return False

    first_arg = args[0]
    cli_commands = {"download", "queue", "config"}

    # Check if first argument is a known CLI command
    if first_arg in cli_commands:
        return True

    # Check for common web server flags
    if first_arg in {"--host", "--port", "--help", "-h"}:
        return False

    return False


def main():
    """Main entry point - route to CLI or Web Server."""
    # Get raw arguments
    raw_args = sys.argv[1:]

    # Determine mode
    if _is_cli_mode(raw_args):
        # Run CLI
        exit_code = CLIApp().run(raw_args)
        sys.exit(exit_code)

    else:
        # Run Web Server
        parser = argparse.ArgumentParser(
            description="O'Reilly Book Downloader - Web Server",
            epilog="Use 'python main.py download --help' for CLI usage",
        )
        parser.add_argument("--host", default="localhost", help="Server host")
        parser.add_argument("--port", type=int, default=8000, help="Server port")
        parser.add_argument("download", nargs="?", help="Download a book (CLI command)")
        parser.add_argument(
            "queue", nargs="?", help="Show download queue (CLI command)"
        )
        args = parser.parse_args(raw_args if raw_args else [])

        print("=" * 50)
        print(" O'Reilly Downloader")
        print("=" * 50)
        print(f"\n  Open http://{args.host}:{args.port} in your browser\n")
        print("  Press Ctrl+C to stop\n")
        print("=" * 50)

        run_server(args.host, args.port)


if __name__ == "__main__":
    main()
