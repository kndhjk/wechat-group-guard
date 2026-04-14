"""
WeChat Group Guard — main entry point (console mode).

Works with MockFileWatcher for demo, or swap in a real
Windows WeChat watcher when desktop integration is ready.
"""

from datetime import datetime

from watcher.mock_file import MockFileWatcher
from detector.scoring import ScoringEngine, THRESHOLD_SUSPICIOUS
from review.queue import ReviewItem
from review.console import ask_for_review, ReviewAction
from storage.jsonl_store import append_jsonl
from storage.pending_store import PendingStore
from storage.decision_store import DecisionStore
from storage.ignore_store import IgnoreStore
from storage.group_store import GroupStore
from watcher.filtering import is_group_allowed
from watcher.dedup import DedupCache


# ── Config ─────────────────────────────────────────────────────────
KEYWORDS = ['加V', '兼职', '刷单', '代写', '贷款', '返利', '推广', '引流', '扫码', '下单']
ALLOWED_GROUPS = ['示例微信群']   # empty list = monitor all

CONFIG_PATH = 'config.yaml'
DATA_DIR = 'data'
LOG_DIR = 'logs'


def load_config():
    """Load keywords, allowed_groups, blocked_domains, trusted_senders from config.yaml."""
    import yaml
    from pathlib import Path
    cfg = {}
    p = Path(CONFIG_PATH)
    if p.exists():
        with open(p, encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
    return cfg


def main():
    cfg = load_config()
    keywords = cfg.get('keywords', KEYWORDS)
    allowed_groups = cfg.get('allowed_groups', ALLOWED_GROUPS)
    blocked_domains = cfg.get('blocked_domains', [])
    trusted_senders = cfg.get('trusted_senders', [])

    # Init components
    watcher = MockFileWatcher('samples/mock_messages.json')
    scoring = ScoringEngine(
        keywords=keywords,
        blocked_domains=blocked_domains,
        trusted_senders=trusted_senders,
    )
    pending_store = PendingStore(f'{DATA_DIR}/pending_reviews.json')
    decision_store = DecisionStore(f'{DATA_DIR}/reviewer_decisions.json')
    ignore_store = IgnoreStore(f'{DATA_DIR}/ignored_users.json')
    dedup = DedupCache(window_seconds=300)

    print('WeChat Group Guard started')
    print(f'Keywords: {keywords}')
    print(f'Groups  : {allowed_groups or "all"}')

    for raw_msg in watcher.poll():
        # Group filter
        if not is_group_allowed(raw_msg.group_name, allowed_groups):
            continue

        # Ignore list
        if ignore_store.contains(raw_msg.sender):
            continue

        # Deduplication
        if dedup.seen(raw_msg.group_name, raw_msg.sender, raw_msg.text, raw_msg.timestamp):
            continue

        # Score
        result = scoring.score(raw_msg.text, sender=raw_msg.sender)

        # Record offender
        if result.suspicious:
            scoring.offender_tracker.record(raw_msg.sender, result.score, raw_msg.timestamp)

        # Log message
        append_jsonl(f'{DATA_DIR}/messages.jsonl', {
            'review_id': result.review_id,
            'group_name': raw_msg.group_name,
            'sender': raw_msg.sender,
            'text': raw_msg.text,
            'reasons': result.reasons,
            'score': result.score,
            'suspicious': result.suspicious,
            'repeated_offense': result.repeated_offense,
            'timestamp': raw_msg.timestamp.isoformat(),
        })

        # Non-suspicious — nothing to do
        if not result.suspicious:
            print(f'  [OK] {raw_msg.sender}: {raw_msg.text[:50]}')
            continue

        # Build review item
        item = ReviewItem(
            group_name=raw_msg.group_name,
            sender=raw_msg.sender,
            message=raw_msg.text,
            reasons=result.reasons,
            score=result.score,
            review_id=result.review_id,
            timestamp=raw_msg.timestamp.isoformat(),
        )

        # Add to pending store for GUI
        pending_store.add(item.to_dict())
        print(f'  [!!] {raw_msg.sender} flagged (score={result.score}): {result.reasons}')

        # Console review
        action = ask_for_review(item)
        if action == ReviewAction.IGNORE_USER:
            ignore_store.add(raw_msg.sender, reason='console_ignore', review_id=result.review_id)
            item.mark_ignored()
            print(f'  [~] {raw_msg.sender} ignored')
        elif action == ReviewAction.KICK:
            item.mark_approved()
            print(f'  [KICK] {raw_msg.sender} from {raw_msg.group_name}')
            # TODO: hand off to executor for real WeChat kick
        else:
            item.mark_skipped()
            print(f'  [SKIP] {raw_msg.sender}')

        # Record decision
        decision = item.to_dict()
        decision['action'] = action.value
        decision['reviewed_at'] = datetime.now().isoformat()
        append_jsonl(f'{LOG_DIR}/review_actions.jsonl', decision)
        decision_store.append(decision)


if __name__ == '__main__':
    main()
