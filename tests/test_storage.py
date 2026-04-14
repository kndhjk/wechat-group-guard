import json
import pytest
import tempfile
import os
from pathlib import Path

from storage.pending_store import PendingStore
from storage.decision_store import DecisionStore
from storage.ignore_store import IgnoreStore, IgnoredUser
from storage.group_store import GroupStore


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestPendingStore:
    def test_load_empty(self, tmp_dir):
        p = PendingStore(str(tmp_dir / 'pending.json'))
        assert p.load() == []

    def test_add_and_load(self, tmp_dir):
        p = PendingStore(str(tmp_dir / 'pending.json'))
        p.add({'sender': 'Spammer', 'group_name': '群A', 'reasons': ['keyword:加V']})
        items = p.load()
        assert len(items) == 1
        assert items[0]['sender'] == 'Spammer'

    def test_save_overwrites(self, tmp_dir):
        p = PendingStore(str(tmp_dir / 'pending.json'))
        p.save([{'sender': 'A'}])
        p.save([{'sender': 'B'}, {'sender': 'C'}])
        assert len(p.load()) == 2


class TestDecisionStore:
    def test_append_and_load(self, tmp_dir):
        d = DecisionStore(str(tmp_dir / 'decisions.json'))
        d.append({'sender': 'X', 'approved': True})
        d.append({'sender': 'Y', 'approved': False})
        data = d.load()
        assert len(data) == 2
        assert data[0]['sender'] == 'X'
        assert data[1]['sender'] == 'Y'


class TestIgnoreStore:
    def test_contains_false_for_empty(self, tmp_dir):
        s = IgnoreStore(str(tmp_dir / 'ignored.json'))
        assert s.contains('Alice') is False

    def test_add_and_contains(self, tmp_dir):
        s = IgnoreStore(str(tmp_dir / 'ignored.json'))
        s.add('Alice', reason='trusted_admin')
        assert s.contains('Alice') is True
        assert s.contains('Bob') is False

    def test_add_duplicate_no_op(self, tmp_dir):
        s = IgnoreStore(str(tmp_dir / 'ignored.json'))
        s.add('Alice')
        s.add('Alice')  # should not raise
        assert len(s.load()) == 1

    def test_remove(self, tmp_dir):
        s = IgnoreStore(str(tmp_dir / 'ignored.json'))
        s.add('Alice')
        s.remove('Alice')
        assert s.contains('Alice') is False

    def test_all_senders(self, tmp_dir):
        s = IgnoreStore(str(tmp_dir / 'ignored.json'))
        s.add('Alice')
        s.add('Bob')
        assert set(s.all_senders()) == {'Alice', 'Bob'}


class TestGroupStore:
    def test_load_empty(self, tmp_dir):
        g = GroupStore(str(tmp_dir / 'groups.json'))
        assert g.load() == []

    def test_save_and_load(self, tmp_dir):
        g = GroupStore(str(tmp_dir / 'groups.json'))
        groups = [{'name': '群A', 'enabled': True}, {'name': '群B', 'enabled': False}]
        g.save(groups)
        loaded = g.load()
        assert len(loaded) == 2
        assert loaded[0]['name'] == '群A'
        assert loaded[0]['enabled'] is True
