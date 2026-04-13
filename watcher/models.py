from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    group_name: str
    sender: str
    text: str
    timestamp: datetime
