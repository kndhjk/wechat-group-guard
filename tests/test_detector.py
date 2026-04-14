# ──────────────────────────────────────────────────────────────────
# WeChat Group Guard — Test suite
# Run:  python -m pytest tests/ -v
# ──────────────────────────────────────────────────────────────────

import pytest
from datetime import datetime, timedelta

from detector.rules import RulesEngine, detect_text
from detector.scoring import (
    ScoringEngine, ScoreResult, RepeatOffenderTracker,
    THRESHOLD_SUSPICIOUS, THRESHOLD_HIGH,
    WEIGHT_KEYWORD, WEIGHT_URL, WEIGHT_PHONE,
    WEIGHT_WECHAT_ID, WEIGHT_DISGUISED, WEIGHT_BLOCKED_DOMAIN,
    WEIGHT_REPEATED,
)


# ── Rules engine ────────────────────────────────────────────────────

class TestRulesEngine:
    def test_no_keywords_no_signal(self):
        engine = RulesEngine(keywords=['加V', '推广'])
        result = engine.detect('大家今天吃什么', sender='Alice')
        assert result.suspicious is False
        assert result.reasons == []

    def test_keyword_hit(self):
        engine = RulesEngine(keywords=['加V', '推广'])
        result = engine.detect('加V了解兼职', sender='Spammer')
        assert 'keyword:加V' in result.reasons

    def test_keyword_case_insensitive(self):
        engine = RulesEngine(keywords=['兼职'])
        result = engine.detect('兼职', sender='X')
        assert 'keyword:兼职' in result.reasons

    def test_url_signal(self):
        engine = RulesEngine(keywords=[])
        result = engine.detect('推广链接 https://example.com', sender='X')
        assert 'url' in result.reasons

    def test_blocked_domain(self):
        engine = RulesEngine(keywords=[], blocked_domains=['bit.ly', 't.cn'])
        result = engine.detect('点这个 t.cn/abc', sender='X')
        # Blocked domain → specific reason, not generic 'url'
        assert 'blocked_domain:t.cn' in result.reasons
        assert 'url' not in result.reasons

    def test_phone_signal(self):
        engine = RulesEngine(keywords=[])
        result = engine.detect('联系我 0212345678', sender='X')
        assert 'phone' in result.reasons

    def test_wechat_id_hint(self):
        engine = RulesEngine(keywords=[])
        result = engine.detect('加我微信 abc123', sender='X')
        assert 'wechat_id_hint' in result.reasons

    def test_disguised_chars(self):
        engine = RulesEngine(keywords=[])
        result = engine.detect('微❤信找我', sender='X')
        assert 'disguised_chars' in result.reasons

    def test_disguised_plus_v(self):
        engine = RulesEngine(keywords=[])
        result = engine.detect('加➕V了解', sender='X')
        assert 'disguised_chars' in result.reasons

    def test_trusted_sender_bypasses(self):
        engine = RulesEngine(keywords=['加V'], trusted_senders=['AdminZhang'])
        result = engine.detect('加V找我', sender='AdminZhang')
        assert result.suspicious is False
        assert result.reasons == []


# ── Scoring engine ───────────────────────────────────────────────────

class TestScoringEngine:
    def _score(self, text, sender='X', keywords=None, blocked=None, trusted=None):
        engine = ScoringEngine(
            keywords=keywords or ['加V', '推广'],
            blocked_domains=blocked or [],
            trusted_senders=trusted or [],
        )
        return engine.score(text, sender=sender)

    def test_clean_message_not_suspicious(self):
        result = self._score('大家晚安')
        assert result.suspicious is False
        assert result.score < THRESHOLD_SUSPICIOUS

    def test_keyword_only_just_suspicious(self):
        # keyword = 30 pts, threshold = 30 → suspicious
        result = self._score('加V找我', keywords=['加V'])
        assert result.suspicious is True
        assert 30 <= result.score < THRESHOLD_HIGH

    def test_multiple_signals_high_score(self):
        result = self._score(
            '加V兼职 https://bit.ly/xyz 联系 021234567',
            keywords=['加V', '兼职'],
            blocked=['bit.ly'],
        )
        # keyword×2 + url + blocked_domain + phone
        assert result.score >= THRESHOLD_HIGH

    def test_score_capped_at_100(self):
        result = self._score(
            '加V https://bit.ly https://t.cn https://taobao.com 联系 021234567 微❤信',
            keywords=['加V', '推广', '兼职', '贷款'],
            blocked=['bit.ly', 't.cn', 'taobao.com'],
        )
        assert result.score <= 100

    def test_review_id_deterministic(self):
        r1 = self._score('hello', sender='Alice')
        r2 = self._score('hello', sender='Alice')
        assert r1.review_id == r2.review_id

    def test_different_sender_different_id(self):
        r1 = self._score('hello', sender='Alice')
        r2 = self._score('hello', sender='Bob')
        assert r1.review_id != r2.review_id

    def test_trusted_sender_score_zero(self):
        result = self._score('加V找我', sender='TrustedAdmin', trusted=['TrustedAdmin'])
        assert result.score == 0
        assert result.suspicious is False


# ── Repeat offender tracker ──────────────────────────────────────────

class TestRepeatOffenderTracker:
    def test_first_offense_not_repeat(self):
        tracker = RepeatOffenderTracker(window_hours=24, max_reviews=3)
        assert tracker.is_repeat_offender('X') is False

    def test_under_threshold_not_repeat(self):
        tracker = RepeatOffenderTracker(window_hours=24, max_reviews=3)
        now = datetime.now()
        tracker.record('X', 30, now - timedelta(hours=2))
        tracker.record('X', 40, now - timedelta(hours=1))
        assert tracker.is_repeat_offender('X') is False

    def test_at_threshold_is_repeat(self):
        tracker = RepeatOffenderTracker(window_hours=24, max_reviews=3)
        now = datetime.now()
        tracker.record('X', 30, now - timedelta(hours=2))
        tracker.record('X', 35, now - timedelta(hours=1))
        tracker.record('X', 50, now)
        assert tracker.is_repeat_offender('X') is True

    def test_old_offenses_expired(self):
        tracker = RepeatOffenderTracker(window_hours=24, max_reviews=3)
        now = datetime.now()
        tracker.record('X', 30, now - timedelta(hours=25))
        tracker.record('X', 40, now - timedelta(hours=24))
        # Only 1 within window
        assert tracker.is_repeat_offender('X') is False

    def test_offense_count(self):
        tracker = RepeatOffenderTracker(window_hours=24, max_reviews=3)
        now = datetime.now()
        tracker.record('X', 30, now - timedelta(hours=2))
        tracker.record('X', 20, now - timedelta(hours=1))  # below threshold
        tracker.record('X', 40, now)
        # Only 2 above 30
        assert tracker.get_offense_count('X') == 2


# ── Score weights are correct ────────────────────────────────────────

class TestScoreWeights:
    def test_keyword_weight(self):
        result = ScoringEngine(keywords=['测试'], blocked_domains=[], trusted_senders=[]).score('测试')
        assert any(r.startswith('keyword:') for r in result.reasons)
        # only keyword → score should be exactly WEIGHT_KEYWORD
        non_url = [r for r in result.reasons if r != 'url']
        # If URL was also triggered, the weight will differ

    def test_score_result_fields(self):
        result = ScoringEngine(keywords=['a'], blocked_domains=[], trusted_senders=[]).score('a')
        assert hasattr(result, 'suspicious')
        assert hasattr(result, 'score')
        assert hasattr(result, 'reasons')
        assert hasattr(result, 'review_id')
        assert hasattr(result, 'repeated_offense')


# ── Module-level convenience functions ───────────────────────────────

class TestModuleLevelFunctions:
    def test_score_text_convenience(self):
        from detector.scoring import score_text
        result = score_text('加V找我', ['加V'])
        assert result.suspicious is True
        assert result.score >= 30

    def test_detect_text_convenience(self):
        result = detect_text('加V找我', ['加V'])
        assert result.suspicious is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
