from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ReviewItem:
    group_name: str
    sender: str
    message: str
    reasons: List[str] = field(default_factory=list)
    status: str = 'pending'          # pending | approved | skipped | ignored
    score: int = 0
    review_id: str = ''
    timestamp: str = ''

    def mark_approved(self) -> None:
        self.status = 'approved'

    def mark_skipped(self) -> None:
        self.status = 'skipped'

    def mark_ignored(self) -> None:
        self.status = 'ignored'

    def to_dict(self) -> dict:
        return {
            'group_name': self.group_name,
            'sender': self.sender,
            'message': self.message,
            'reasons': self.reasons,
            'status': self.status,
            'score': self.score,
            'review_id': self.review_id,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'ReviewItem':
        return cls(
            group_name=d.get('group_name', ''),
            sender=d.get('sender', ''),
            message=d.get('message', ''),
            reasons=d.get('reasons', []),
            status=d.get('status', 'pending'),
            score=d.get('score', 0),
            review_id=d.get('review_id', ''),
            timestamp=d.get('timestamp', ''),
        )
