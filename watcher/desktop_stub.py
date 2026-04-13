from typing import Iterable
from .base import MessageWatcher
from .models import ChatMessage


class DesktopWeChatWatcher(MessageWatcher):
    """
    Placeholder for a real desktop WeChat watcher.

    Planned implementations:
    - Windows UI Automation first
    - optional OCR fallback
    - group whitelist filtering
    """

    def __init__(self, group_names: list[str] | None = None):
        self.group_names = group_names or []

    def poll(self) -> Iterable[ChatMessage]:
        # TODO: hook into desktop WeChat UI tree and read newly appeared messages
        return []
