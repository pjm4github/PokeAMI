"""In-process event log with ring buffer for simulator events.

Captures component start/stop, query, and error events for the
dashboard control panel.
"""

from collections import deque
from datetime import datetime, timezone


class EventLog:
    """Ring-buffer event log for simulator component activity."""

    def __init__(self, maxlen: int = 200):
        self._buffer: deque[dict] = deque(maxlen=maxlen)

    def append(self, component: str, message: str, level: str = "info") -> None:
        self._buffer.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "component": component,
            "message": message,
        })

    def tail(self, n: int = 50) -> list[dict]:
        items = list(self._buffer)
        return items[-n:]

    def clear(self) -> None:
        self._buffer.clear()
