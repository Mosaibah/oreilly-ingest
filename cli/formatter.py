"""Formatting utilities for CLI progress display."""

import time
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressState:
    """Holds progress state for display."""

    status: str = ""
    percentage: int = 0
    message: str = ""
    current_chapter: int = 0
    total_chapters: int = 0
    chapter_title: str = ""
    start_time: float = 0

    def get_eta_seconds(self) -> Optional[int]:
        """Calculate ETA in seconds."""
        if self.start_time == 0 or self.percentage <= 0:
            return None

        elapsed = time.time() - self.start_time
        rate = self.percentage / elapsed
        remaining_percent = 100 - self.percentage
        eta = remaining_percent / rate if rate > 0 else None

        return int(eta) if eta else None


class CliFormatter:
    """Format and display CLI output."""

    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "dim": "\033[2m",
    }

    # Progress bar symbols
    BAR_FILLED = "█"
    BAR_EMPTY = "░"

    @staticmethod
    def colored(text: str, color: str) -> str:
        """Return colored text if stdout is a TTY."""
        if not sys.stdout.isatty():
            return text

        color_code = CliFormatter.COLORS.get(color, "")
        reset = CliFormatter.COLORS["reset"]
        return f"{color_code}{text}{reset}"

    @staticmethod
    def progress_bar(percentage: int, width: int = 40) -> str:
        """
        Create a progress bar.

        Args:
            percentage: Progress percentage (0-100).
            width: Width of the bar.

        Returns:
            Formatted progress bar string.
        """
        filled = int(width * percentage / 100)
        empty = width - filled

        bar = CliFormatter.BAR_FILLED * filled + CliFormatter.BAR_EMPTY * empty

        return f"[{bar}] {percentage:3d}%"

    @staticmethod
    def format_time(seconds: int) -> str:
        """Format seconds into readable time string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    @staticmethod
    def format_file_size(bytes_size: int) -> str:
        """Format bytes into readable size string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    @staticmethod
    def print_progress(state: ProgressState):
        """
        Print progress to stdout.

        Args:
            state: ProgressState object.
        """
        # Build status line
        status_display = CliFormatter.colored(state.status.upper(), "cyan")

        # Build progress bar
        bar = CliFormatter.progress_bar(state.percentage)

        # Build ETA
        eta = state.get_eta_seconds()
        eta_str = f"ETA: {CliFormatter.format_time(eta)}" if eta else ""

        # Build chapter info
        chapter_str = ""
        if state.total_chapters > 0:
            chapter_str = f" | Ch {state.current_chapter}/{state.total_chapters}"
            if state.chapter_title:
                chapter_str += f": {state.chapter_title[:30]}"

        # Print to stdout
        message = f"{status_display} {bar} {eta_str}{chapter_str}"
        if state.message:
            message += f" | {state.message}"

        # Use \r for inline updates, add newline at end
        print(message, end="\r")
        sys.stdout.flush()

    @staticmethod
    def print_complete(message: str):
        """Print completion message."""
        msg = CliFormatter.colored("✓", "green") + f" {message}"
        print(msg)

    @staticmethod
    def print_error(message: str):
        """Print error message."""
        msg = CliFormatter.colored("✗", "red") + f" {message}"
        print(msg)

    @staticmethod
    def print_info(message: str):
        """Print info message."""
        msg = CliFormatter.colored("ℹ", "blue") + f" {message}"
        print(msg)

    @staticmethod
    def print_warning(message: str):
        """Print warning message."""
        msg = CliFormatter.colored("⚠", "yellow") + f" {message}"
        print(msg)

    @staticmethod
    def print_table(
        headers: list[str], rows: list[list[str]], widths: Optional[list[int]] = None
    ):
        """
        Print a formatted table.

        Args:
            headers: List of header strings.
            rows: List of rows (each row is a list of strings).
            widths: Optional column widths. If None, auto-calculate.
        """
        if not headers or not rows:
            return

        # Auto-calculate widths if not provided
        if widths is None:
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(str(cell)))

        # Print header
        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(CliFormatter.colored(header_line, "bold"))
        print("-" * len(header_line))

        # Print rows
        for row in rows:
            row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
            print(row_line)
