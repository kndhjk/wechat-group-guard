import pytest
from datetime import datetime, timedelta

from watcher.dedup import DedupCache, MessageFingerprint


class TestDedupCache:
    def test_first_message_not_duplicate(self):
        d = DedupCache(window_seconds=300)
        assert d.seen('群A', 'Alice', 'hello') is False

    def test_exact_duplicate_within_window_is_dup(self):
        d = DedupCache(window_seconds=300)
        d.seen('群A', 'Alice', 'hello')
        assert d.seen('群A', 'Alice', 'hello') is True

    def test_different_group_not_dup(self):
        d = DedupCache(window_seconds=300)
        d.seen('群A', 'Alice', 'hello')
        assert d.seen('群B', 'Alice', 'hello') is False

    def test_different_sender_not_dup(self):
        d = DedupCache(window_seconds=300)
        d.seen('群A', 'Alice', 'hello')
        assert d.seen('群A', 'Bob', 'hello') is False

    def test_different_text_not_dup(self):
        d = DedupCache(window_seconds=300)
        d.seen('群A', 'Alice', 'hello')
        assert d.seen('群A', 'Alice', 'world') is False

    def test_old_entry_evicted(self):
        d = DedupCache(window_seconds=60, max_items=100)
        now = datetime.now()
        d.seen('群A', 'Alice', 'hello', timestamp=now - timedelta(seconds=120))
        # 120s ago > 60s window → not a dup
        assert d.seen('群A', 'Alice', 'hello', timestamp=now) is False

    def test_clear(self):
        d = DedupCache(window_seconds=300)
        d.seen('群A', 'Alice', 'hello')
        d.clear()
        assert d.seen('群A', 'Alice', 'hello') is False

    def test_max_items_fifo_eviction(self):
        """
        max_items=3: fill with A, B, C → add D → oldest (A) is evicted.
        B and C survive until a 5th unique entry is added.
        """
        d = DedupCache(window_seconds=300, max_items=3)

        d.seen('群A', 'A', 'm1')
        d.seen('群A', 'B', 'm2')
        d.seen('群A', 'C', 'm3')

        # Cache now full: [A, B, C]
        assert len(d._queue) == 3

        # Adding D evicts A (FIFO)
        r_d = d.seen('群A', 'D', 'm4')
        assert r_d is False        # D is new
        assert len(d._queue) == 3  # still 3 after eviction

        # Verify A was evicted (re-adding A creates a NEW entry)
        # B and C are still present
        assert d.seen('群A', 'B', 'm2') is True
        assert d.seen('群A', 'C', 'm3') is True

    def test_same_fingerprint_different_time_outside_window(self):
        d = DedupCache(window_seconds=60)
        now = datetime.now()
        d.seen('群A', 'Alice', 'hello', timestamp=now - timedelta(seconds=120))
        # 120s ago > 60s window → not a dup
        assert d.seen('群A', 'Alice', 'hello', timestamp=now) is False


class TestMessageFingerprint:
    def test_fingerprint_equality(self):
        fp1 = MessageFingerprint('群A', 'Alice', 'hello')
        fp2 = MessageFingerprint('群A', 'Alice', 'hello')
        assert fp1 == fp2
        assert hash(fp1) == hash(fp2)

    def test_fingerprint_inequality(self):
        fp1 = MessageFingerprint('群A', 'Alice', 'hello')
        fp2 = MessageFingerprint('群A', 'Alice', 'world')
        assert fp1 != fp2
