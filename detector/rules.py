import re
from dataclasses import dataclass
from typing import List


URL_RE = re.compile(r'https?://|www\\.')
PHONE_RE = re.compile(r'(?:\\+?64|0)\\d{8,11}')
WECHAT_ID_RE = re.compile(r'微信|vx|v信|wechat', re.IGNORECASE)


@dataclass
class DetectionResult:
    suspicious: bool
    reasons: List[str]


def detect_text(text: str, keywords: list[str]) -> DetectionResult:
    reasons: list[str] = []
    low = text.lower()
    for kw in keywords:
        if kw.lower() in low:
            reasons.append(f'keyword:{kw}')
    if URL_RE.search(text):
        reasons.append('url')
    if PHONE_RE.search(text):
        reasons.append('phone')
    if WECHAT_ID_RE.search(text):
        reasons.append('wechat_id_hint')
    return DetectionResult(suspicious=bool(reasons), reasons=reasons)
