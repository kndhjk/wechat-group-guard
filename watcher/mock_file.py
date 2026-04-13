import json
from datetime import datetime
from pathlib import Path
from .base import MessageWatcher
from .models import ChatMessage


class MockFileWatcher(MessageWatcher):
    def __init__(self, path: str):
        self.path = Path(path)
        self._drained = False

    def poll(self):
        if self._drained:
            return []
        self._drained = True
        data = json.loads(self.path.read_text(encoding='utf-8'))
        return [
            ChatMessage(
                group_name=item['group_name'],
                sender=item['sender'],
                text=item['text'],
                timestamp=datetime.now(),
            )
            for item in data
        ]
