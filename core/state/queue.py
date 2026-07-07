"""Queue management for multiple book downloads."""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Optional

import config


@dataclass
class QueueItem:
    """Represents a single queued download task."""

    id: str
    book_id: str
    formats: list[str]
    output_dir: str
    all_chapters: bool = True
    selected_chapters: Optional[list[int]] = None
    skip_images: bool = False
    chunk_size: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        """Create from dictionary."""
        return cls(**data)


class QueueManager:
    """Manage a queue of book downloads."""

    def __init__(self, queue_file: Optional[Path] = None):
        """
        Initialize queue manager.

        Args:
            queue_file: Path to queue file. Defaults to config.QUEUE_FILE.
        """
        self.queue_file = queue_file or config.QUEUE_FILE
        self.queue: list[QueueItem] = []
        self._lock = RLock()
        self._load_queue()

    def _load_queue(self):
        """Load queue from file. Resets to empty if file is missing, empty, or corrupted."""
        with self._lock:
            if not self.queue_file.exists():
                self.queue = []
                return

            try:
                raw = self.queue_file.read_text(encoding="utf-8").strip()
                if not raw:
                    self.queue = []
                    return
                data = json.loads(raw)
                if not isinstance(data, list):
                    self.queue = []
                    return
                self.queue = [QueueItem.from_dict(item) for item in data]
            except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                self.queue = []

    def _save_queue(self):
        """Save queue to file atomically (write to tmp, then rename)."""
        with self._lock:
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.queue_file.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps([item.to_dict() for item in self.queue], indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.queue_file)

    def add(self, item: QueueItem) -> str:
        """
        Add item to queue.

        Args:
            item: QueueItem to add.

        Returns:
            ID of the queued item.
        """
        with self._lock:
            self.queue.append(item)
            self._save_queue()
        return item.id

    def remove(self, item_id: str) -> bool:
        """
        Remove item from queue.

        Args:
            item_id: ID of item to remove.

        Returns:
            True if item was removed, False if not found.
        """
        with self._lock:
            initial_len = len(self.queue)
            self.queue = [item for item in self.queue if item.id != item_id]

            if len(self.queue) < initial_len:
                self._save_queue()
                return True
            return False

    def get(self, item_id: str) -> Optional[QueueItem]:
        """Get item by ID."""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    return item
        return None

    def list_pending(self) -> list[QueueItem]:
        """Get all pending items."""
        with self._lock:
            return [item for item in self.queue if item.status == "pending"]

    def list_all(self) -> list[QueueItem]:
        """Get all items."""
        with self._lock:
            return list(self.queue)

    def update_status(
        self, item_id: str, status: str, error_message: Optional[str] = None
    ):
        """
        Update item status.

        Args:
            item_id: ID of item to update.
            status: New status (pending, processing, completed, failed).
            error_message: Error message if status is failed.
        """
        with self._lock:
            item = self.get(item_id)
            if item:
                item.status = status
                item.error_message = error_message
                self._save_queue()

    def clear_completed(self):
        """Remove all completed items from queue."""
        with self._lock:
            self.queue = [item for item in self.queue if item.status != "completed"]
            self._save_queue()
