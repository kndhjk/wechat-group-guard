from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageFingerprint:
    group_name: str
    sender: str
    text: str


class DedupCache:
    def __init__(self, max_items: int = 500):
        self.max_items = max_items
        self._queue = deque()
        self._set = set()

    def seen(self, group_name: str, sender: str, text: str) -> bool:
        fp = MessageFingerprint(group_name, sender, text)
        if fp in self._set:
            return True
        self._queue.append(fp)
        self._set.add(fp)
        while len(self._queue) > self.max_items:
            old = self._queue.popleft()
            self._set.discard(old)
        return False
