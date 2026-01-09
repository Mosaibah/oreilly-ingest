"""File system utilities."""

import re


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a cross-platform filename."""
    name = name.replace("/", "-").replace("\\", "-")
    name = name.replace(":", " -").replace("?", "").replace("*", "")
    name = name.replace('"', "'").replace("<", "").replace(">", "")
    name = name.replace("|", "-")
    name = name.strip().strip(".")
    if len(name) > 200:
        name = name[:200].strip()
    return name


def slugify(name: str) -> str:
    """Convert a string to a URL-friendly slug for folder names."""
    name = name.lower()
    name = re.sub(r"['\"]", "", name)
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    if len(name) > 100:
        name = name[:100].rstrip("-")
    return name
