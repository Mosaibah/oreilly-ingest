"""Shared type definitions for client-agnostic API contracts.

This module defines the data structures used across all plugins
and interfaces (web, CLI, scripts). These types ensure consistent
data exchange regardless of the client.
"""

from typing import TypedDict


class ChapterInfo(TypedDict):
    """Full chapter metadata returned by ChaptersPlugin.fetch_list()."""

    ourn: str
    title: str
    filename: str
    content_url: str
    images: list[str]
    stylesheets: list[str]
    virtual_pages: int | None
    minutes_required: float | None


class ChapterSummary(TypedDict):
    """Simplified chapter info for client display (e.g., chapter picker UI)."""

    index: int
    title: str
    pages: int | None
    minutes: float | None


class BookInfo(TypedDict, total=False):
    """Book metadata returned by BookPlugin.fetch().

    Note: Uses total=False because not all fields are always present.
    """

    book_id: str
    title: str
    authors: list[str]
    publisher: str
    cover_url: str | None
    description: str
    isbn: str | None
    topics: list[str]
    pages: int | None


class FormatInfo(TypedDict):
    """Format metadata for discovery endpoints."""

    name: str
    description: str
    supports_chapters: bool
    aliases: list[str]
