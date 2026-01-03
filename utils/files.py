"""File system utilities."""

import re


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.

    Removes or replaces characters that are invalid in filenames
    across different operating systems.
    """
    # Replace problematic characters with safe alternatives
    name = name.replace("/", "-").replace("\\", "-")
    name = name.replace(":", " -").replace("?", "").replace("*", "")
    name = name.replace('"', "'").replace("<", "").replace(">", "")
    name = name.replace("|", "-")
    # Remove leading/trailing whitespace and dots
    name = name.strip().strip(".")
    # Limit length to avoid filesystem issues
    if len(name) > 200:
        name = name[:200].strip()
    return name


def slugify(name: str) -> str:
    """
    Convert a string to a URL-friendly slug.

    Used for creating folder names from book titles.
    """
    name = name.lower()
    name = re.sub(r"['\"]", "", name)
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    if len(name) > 100:
        name = name[:100].rstrip("-")
    return name
