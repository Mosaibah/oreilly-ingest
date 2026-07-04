"""Compatibility wrapper for queue state helpers now owned by core.state."""

from core.state.queue import QueueItem, QueueManager

__all__ = ["QueueItem", "QueueManager"]
