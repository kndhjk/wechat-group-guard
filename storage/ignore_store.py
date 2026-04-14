from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class IgnoredUser:
    sender: str
    reason: str = ''
    ignored_at: str = ''
    review_id: str = ''

    def to_dict(self) -> dict:
        return {
            'sender': self.sender,
            'reason': self.reason,
            'ignored_at': self.ignored_at,
            'review_id': self.review_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'IgnoredUser':
        return cls(
            sender=d.get('sender', ''),
            reason=d.get('reason', ''),
            ignored_at=d.get('ignored_at', ''),
            review_id=d.get('review_id', ''),
        )


class IgnoreStore:
    """
    Persistent store for ignored (whitelisted) users.
    Once ignored, a user's messages will skip detection entirely.
    """

    def __init__(self, path: str = 'data/ignored_users.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def load(self) -> list[IgnoredUser]:
        raw = json.loads(self.path.read_text(encoding='utf-8'))
        return [IgnoredUser.from_dict(d) for d in raw]

    def save(self, items: list[IgnoredUser]) -> None:
        data = [item.to_dict() for item in items]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def contains(self, sender: str) -> bool:
        return any(u.sender == sender for u in self.load())

    def add(self, sender: str, reason: str = '', review_id: str = '') -> None:
        items = self.load()
        if any(u.sender == sender for u in items):
            return  # already ignored
        items.append(IgnoredUser(
            sender=sender,
            reason=reason,
            ignored_at=datetime.now().isoformat(),
            review_id=review_id,
        ))
        self.save(items)

    def remove(self, sender: str) -> None:
        items = [u for u in self.load() if u.sender != sender]
        self.save(items)

    def all_senders(self) -> list[str]:
        return [u.sender for u in self.load()]
