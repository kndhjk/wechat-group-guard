from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set


# Matches http://, https://, www., and bare short domains (t.cn, bit.ly, vm.tiktok.com …)
URL_RE = re.compile(
    r'https?://|www\.|[\w-]+\.(?:cn|com|org|net|io|ai|cc|co|me|info|pro|top|xyz|tv|cc|go)\b',
    re.IGNORECASE
)
PHONE_RE = re.compile(r'(?:\+?64|0)\d{8,11}')
WECHAT_ID_RE = re.compile(r'微信|vx|v信|wechat', re.IGNORECASE)
# Match anything that looks like a WeChat ID (alphanumeric, 6-30 chars, after @ or standalone)
WECHAT_MENTION_RE = re.compile(r'@?\b[a-zA-Z][a-zA-Z0-9_.-]{5,29}\b')

# Default blocked domains (simple list, case-insensitive matching)
DEFAULT_BLOCKED_DOMAINS: Set[str] = {
    't.cn', 'bit.ly', 'tinyurl.com', 'goo.gl',
    'taobao.com', '1688.com', 'pinduoduo.com', '拼多多',
}


@dataclass
class DetectionResult:
    suspicious: bool
    reasons: List[str]


class RulesEngine:
    def __init__(
        self,
        keywords: List[str] = [],
        blocked_domains: List[str] = [],
        trusted_senders: List[str] = [],
    ):
        self.keywords = keywords
        self.blocked_domains: Set[str] = set(d.lower() for d in blocked_domains) | DEFAULT_BLOCKED_DOMAINS
        self.trusted_senders: Set[str] = set(trusted_senders)

    def detect(self, text: str, sender: str = '') -> DetectionResult:
        reasons: list[str] = []

        # Trusted senders always pass
        if sender in self.trusted_senders:
            return DetectionResult(suspicious=False, reasons=[])

        low = text.lower()

        # Keyword hits
        for kw in self.keywords:
            if kw.lower() in low:
                reasons.append(f'keyword:{kw}')

        # URL detection (broader: handles bare short domains like t.cn, bit.ly)
        found_url = False
        for m in URL_RE.finditer(text):
            found_url = True
            matched_domain = m.group(0).lower().rstrip('/').lstrip('https://').lstrip('http://').lstrip('www.')
            for blocked in self.blocked_domains:
                if blocked in matched_domain or blocked in m.group(0).lower():
                    reasons.append(f'blocked_domain:{blocked}')
                    break
        if found_url and 'blocked_domain:' not in ' '.join(reasons):
            reasons.append('url')

        # Phone number
        if PHONE_RE.search(text):
            reasons.append('phone')

        # WeChat ID hint
        if WECHAT_ID_RE.search(text):
            reasons.append('wechat_id_hint')

        # Repeated character detection (e.g. "加➕V" or "微❤信")
        if self._has_disguised_chars(low):
            reasons.append('disguised_chars')

        return DetectionResult(suspicious=bool(reasons), reasons=reasons)

    def _has_disguised_chars(self, text: str) -> bool:
        """Detect Chinese/English character substitution (e.g. 微✨信, 加➕V)."""
        disguised_patterns = [
            r'微.*信', r'加.*V', r'私.*我', r'联.*我',
            r'[➕✨⭐❤🔴🟠🟡🟢🔵🟣]+', r'【.*】',
        ]
        for pat in disguised_patterns:
            if re.search(pat, text):
                return True
        return False


# Module-level convenience
_default_engine = RulesEngine(keywords=[])

def detect_text(text: str, keywords: list[str]) -> DetectionResult:
    _default_engine.keywords = list(keywords)
    return _default_engine.detect(text)

def set_keywords(keywords: list[str]) -> None:
    _default_engine.keywords = keywords

def set_blocked_domains(domains: list[str]) -> None:
    _default_engine.blocked_domains = set(d.lower() for d in domains) | DEFAULT_BLOCKED_DOMAINS

def set_trusted_senders(senders: list[str]) -> None:
    _default_engine.trusted_senders = set(senders)
