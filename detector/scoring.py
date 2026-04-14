from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set
from collections import defaultdict
from datetime import datetime, timedelta

from detector.rules import RulesEngine, DEFAULT_BLOCKED_DOMAINS


# Score weights
WEIGHT_KEYWORD = 30
WEIGHT_URL = 35
WEIGHT_BLOCKED_DOMAIN = 45
WEIGHT_PHONE = 35
WEIGHT_WECHAT_ID = 25
WEIGHT_DISGUISED = 40
WEIGHT_REPEATED = 20

THRESHOLD_SUSPICIOUS = 30
# Scores above HIGH_THRESHOLD are auto-flagged without needing multiple signals
THRESHOLD_HIGH = 60


@dataclass
class ScoreResult:
    suspicious: bool
    score: int
    reasons: list[str]
    review_id: str = ''
    repeated_offense: bool = False


class RepeatOffenderTracker:
    """Track senders who trigger multiple reviews across a time window."""

    def __init__(self, window_hours: int = 24, max_reviews: int = 3):
        self.window = timedelta(hours=window_hours)
        self.max_reviews = max_reviews
        # sender -> list of (timestamp, score)
        self._records: dict[str, list[tuple[datetime, int]]] = defaultdict(list)

    def record(self, sender: str, score: int, timestamp: datetime = None) -> None:
        ts = timestamp or datetime.now()
        self._records[sender].append((ts, score))
        # Prune old records
        cutoff = ts - self.window
        self._records[sender] = [
            (t, s) for (t, s) in self._records[sender] if t > cutoff
        ]

    def is_repeat_offender(self, sender: str) -> bool:
        records = self._records.get(sender, [])
        count = len([s for (t, s) in records if s >= THRESHOLD_SUSPICIOUS])
        return count >= self.max_reviews

    def get_offense_count(self, sender: str) -> int:
        return len([s for (t, s) in self._records.get(sender, []) if s >= THRESHOLD_SUSPICIOUS])


# Global tracker instance (reset per session; could be persisted)
_offender_tracker = RepeatOffenderTracker()


def set_offender_tracker(tracker: RepeatOffenderTracker) -> None:
    global _offender_tracker
    _offender_tracker = tracker


class ScoringEngine:
    def __init__(
        self,
        keywords: List[str] = [],
        blocked_domains: List[str] = [],
        trusted_senders: List[str] = [],
        offender_tracker: RepeatOffenderTracker = None,
    ):
        self.rules = RulesEngine(
            keywords=keywords,
            blocked_domains=blocked_domains,
            trusted_senders=trusted_senders,
        )
        self.offender_tracker = offender_tracker or _offender_tracker

    def score(self, text: str, sender: str = '') -> ScoreResult:
        import hashlib

        result = self.rules.detect(text, sender)
        score = 0
        reasons: list[str] = []

        for reason in result.reasons:
            if reason.startswith('keyword:'):
                score += WEIGHT_KEYWORD
                reasons.append(reason)
            elif reason == 'url':
                score += WEIGHT_URL
                reasons.append(reason)
            elif reason.startswith('blocked_domain:'):
                score += WEIGHT_BLOCKED_DOMAIN
                reasons.append(reason)
            elif reason == 'phone':
                score += WEIGHT_PHONE
                reasons.append(reason)
            elif reason == 'wechat_id_hint':
                score += WEIGHT_WECHAT_ID
                reasons.append(reason)
            elif reason == 'disguised_chars':
                score += WEIGHT_DISGUISED
                reasons.append(reason)
            else:
                score += 10
                reasons.append(reason)

        # Repeated offense bonus
        repeated = False
        if self.offender_tracker.is_repeat_offender(sender):
            score += WEIGHT_REPEATED
            reasons.append('repeat_offender')
            repeated = True

        # Cap at 100
        score = min(score, 100)

        suspicious = score >= THRESHOLD_SUSPICIOUS

        review_id = hashlib.sha1(f'{sender}|{text}'.encode()).hexdigest()[:12]

        return ScoreResult(
            suspicious=suspicious,
            score=score,
            reasons=reasons,
            review_id=review_id,
            repeated_offense=repeated,
        )


# Module-level convenience
_scoring_engine = ScoringEngine()


def score_text(text: str, keywords: list[str], sender: str = '') -> ScoreResult:
    _scoring_engine.rules.keywords = keywords
    return _scoring_engine.score(text, sender)


def configure(keywords=None, blocked_domains=None, trusted_senders=None):
    if keywords is not None:
        _scoring_engine.rules.keywords = keywords
    if blocked_domains is not None:
        _scoring_engine.rules.blocked_domains = set(b.lower() for b in blocked_domains) | DEFAULT_BLOCKED_DOMAINS
    if trusted_senders is not None:
        _scoring_engine.rules.trusted_senders = set(trusted_senders)
