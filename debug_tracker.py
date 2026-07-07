"""In-memory trace and debug logger for Study Agent."""

import threading
from datetime import datetime
from typing import Any


class DebugTracker:
    _lock = threading.Lock()
    _events: list[dict[str, Any]] = []

    @classmethod
    def add_event(cls, event_type: str, details: dict[str, Any]) -> None:
        """Add a debug event in a thread-safe manner."""
        with cls._lock:
            cls._events.append(
                {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "event_type": event_type,  # "mcts_search", "graph_rag", etc.
                    "details": details,
                }
            )
            if len(cls._events) > 50:
                cls._events.pop(0)

    @classmethod
    def get_events(cls) -> list[dict[str, Any]]:
        """Retrieve all tracked debug events, newest first."""
        with cls._lock:
            return list(reversed(cls._events))

    @classmethod
    def clear(cls) -> None:
        """Clear all events."""
        with cls._lock:
            cls._events.clear()
