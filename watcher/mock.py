from datetime import datetime
from typing import Iterable
from .base import MessageWatcher
from .models import ChatMessage


class MockWatcher(MessageWatcher):
    def __init__(self, samples: list[dict] | None = None):
        self.samples = samples or []
        self._drained = False

    def poll(self) -> Iterable[ChatMessage]:
        if self._drained:
            return []
        self._drained = True
        return [
            ChatMessage(
                group_name=item['group_name'],
                sender=item['sender'],
                text=item['text'],
                timestamp=datetime.now(),
            )
            for item in self.samples
        ]
