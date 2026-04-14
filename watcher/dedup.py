from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class MessageFingerprint:
    group_name: str
    sender: str
    text: str


@dataclass
class DedupEntry:
    fp: MessageFingerprint
    timestamp: datetime


class DedupCache:
    """
    Deduplicate messages within a time window.

    Two messages are considered duplicates if they share the same
    (group_name, sender, text) AND occur within `window_seconds`.
    """

    def __init__(self, max_items: int = 500, window_seconds: int = 300):
        self.max_items = max_items
        self.window = timedelta(seconds=window_seconds)
        self._queue: deque[DedupEntry] = deque()
        self._set: set[MessageFingerprint] = set()

    def seen(self, group_name: str, sender: str, text: str, timestamp: Optional[datetime] = None) -> bool:
        ts = timestamp or datetime.now()
        fp = MessageFingerprint(group_name, sender, text)

        # Check if this exact fingerprint is still within the window
        if fp in self._set:
            # Find the entry and check if it's still fresh
            for entry in self._queue:
                if entry.fp == fp and (ts - entry.timestamp) < self.window:
                    return True  # Duplicate within window

        # Not a duplicate (or outside window) — record it
        self._queue.append(DedupEntry(fp=fp, timestamp=ts))
        self._set.add(fp)

        # Evict oldest entries if over capacity
        while len(self._queue) > self.max_items:
            old = self._queue.popleft()
            self._set.discard(old.fp)

        # Also prune entries outside the window
        cutoff = ts - self.window
        while self._queue and self._queue[0].timestamp < cutoff:
            old = self._queue.popleft()
            self._set.discard(old.fp)

        return False

    def clear(self) -> None:
        self._queue.clear()
        self._set.clear()
