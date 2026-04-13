from dataclasses import dataclass, field
from typing import List


@dataclass
class ReviewItem:
    group_name: str
    sender: str
    message: str
    reasons: List[str] = field(default_factory=list)
    status: str = 'pending'
