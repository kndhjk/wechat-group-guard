"""
WeChat Group Guard — main entry point.

Modes:
  --mode mock    Poll mock data once (for testing)
  --mode poll     Continuous poll from WeChat desktop (real)
  --mode gui      Launch the Tkinter review GUI (default)

Config is loaded from config.yaml in the project root.
All paths are relative to the working directory.

Example config.yaml:
    keywords:
      - 加V
      - 兼职
      - 刷单
      - 推广
    allowed_groups:
      - 我的群
      - 同学群
    blocked_domains:
      - t.cn
      - bit.ly
    trusted_senders:
      - AdminZhang
    poll_interval: 5          # seconds between polls
    dry_run: true             # true = never actually kick (safe mode)
    # Set to false only when you have tested dry_run and are ready
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from detector.scoring import ScoringEngine
from detector.rules import DEFAULT_BLOCKED_DOMAINS
from review.console import ask_for_review, ReviewAction
from storage.jsonl_store import append_jsonl
from storage.pending_store import PendingStore
from storage.decision_store import DecisionStore
from storage.ignore_store import IgnoreStore
from storage.group_store import GroupStore
from storage.log_rotation import RotatingJSONLWriter, rotate_logs
from watcher.filtering import is_group_allowed
from watcher.dedup import DedupCache
from executor import DesktopWeChatKickExecutor

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('wcg')


# ── Config loading ──────────────────────────────────────────────────
def load_config() -> dict:
    cfg: dict = {
        'keywords': ['加V', '兼职', '刷单', '代写', '贷款', '返利', '推广', '引流', '扫码', '下单'],
        'allowed_groups': [],
        'blocked_domains': [],
        'trusted_senders': [],
        'poll_interval': 5.0,
        'dry_run': True,
    }
    p = Path('config.yaml')
    if p.exists():
        try:
            import yaml
            with open(p, encoding='utf-8') as f:
                raw = yaml.safe_load(f) or {}
            # Merge only known keys
            for key in cfg:
                if key in raw:
                    cfg[key] = raw[key]
        except ImportError:
            logger.warning('yaml not installed; config.yaml will be ignored')
        except Exception as e:
            logger.warning('Failed to load config.yaml: %s', e)
    return cfg


# ── Watcher factory ─────────────────────────────────────────────────
def make_watcher(cfg: dict, group_store: GroupStore):
    """
    Return the appropriate watcher based on config / availability.

    If Windows WeChat + uiautomation is available and no groups are
    explicitly whitelisted, try the real WeChat watcher.
    Otherwise fall back to MockFileWatcher with sample data.
    """
    # Load enabled groups from group_store
    group_records = group_store.load()
    enabled_groups = [g['name'] for g in group_records if g.get('enabled', False)]
    groups_param = enabled_groups or list(cfg.get('allowed_groups', []))

    # Try real WeChat watcher
    try:
        from watcher.windows_wechat import WeChatWatcher
        w = WeChatWatcher(
            groups=groups_param,
            poll_interval=cfg.get('poll_interval', 5.0),
        )
        if w._probe.is_available():
            logger.info('Using WeChat desktop watcher (real)')
            return w
        else:
            logger.info('WeChat not detected; falling back to mock watcher')
    except Exception as e:
        logger.info('WeChat watcher unavailable (%s); using mock', e)

    # Fall back to mock
    from watcher.mock_file import MockFileWatcher
    logger.info('Using MockFileWatcher (demo mode)')
    return MockFileWatcher('samples/mock_messages.json')


# ── Core processing ────────────────────────────────────────────────
def process_message(msg, scoring, pending_store, decision_store,
                    ignore_store, dedup, executor, allowed_groups, cfg,
                    audit_writer=None):
    """Score, review, and act on a single message. Returns action taken."""
    # Group filter
    if not is_group_allowed(msg.group_name, allowed_groups):
        return None

    # Ignore list
    if ignore_store.contains(msg.sender):
        return None

    # Deduplication (5-minute window)
    if dedup.seen(msg.group_name, msg.sender, msg.text, msg.timestamp):
        return None

    # Score
    result = scoring.score(msg.text, sender=msg.sender)

    # Record repeat offender
    if result.suspicious:
        scoring.offender_tracker.record(msg.sender, result.score, msg.timestamp)

    # Log message
    append_jsonl('data/messages.jsonl', {
        'review_id': result.review_id,
        'group_name': msg.group_name,
        'sender': msg.sender,
        'text': msg.text,
        'reasons': result.reasons,
        'score': result.score,
        'suspicious': result.suspicious,
        'repeated_offense': result.repeated_offense,
        'timestamp': msg.timestamp.isoformat(),
    })

    if not result.suspicious:
        logger.debug('OK %s: %s', msg.sender, msg.text[:40])
        return None

    # Build review item
    from review.queue import ReviewItem
    item = ReviewItem(
        group_name=msg.group_name,
        sender=msg.sender,
        message=msg.text,
        reasons=result.reasons,
        score=result.score,
        review_id=result.review_id,
        timestamp=msg.timestamp.isoformat(),
    )

    # Add to persistent pending queue (for GUI)
    pending_store.add(item.to_dict())
    logger.warning('!! FLAGGED [%dpts] %s in %s: %s',
                   result.score, msg.sender, msg.group_name, result.reasons)

    # Console review
    action = ask_for_review(item)
    reviewed_at = datetime.now().isoformat()

    if action == ReviewAction.IGNORE_USER:
        ignore_store.add(msg.sender, reason='console_ignore', review_id=result.review_id)
        item.mark_ignored()
        logger.info('~ ignored %s', msg.sender)

    elif action == ReviewAction.KICK:
        item.mark_approved()
        # Execute kick (dry_run by default)
        dry_run = cfg.get('dry_run', True)
        if dry_run:
            logger.info('[DRY RUN] Would kick %s from %s', msg.sender, msg.group_name)
        else:
            outcome = executor.kick(msg.group_name, msg.sender)
            logger.info('Kick result: %s', outcome['message'])

    else:  # SKIP
        item.mark_skipped()
        logger.info('skipped %s', msg.sender)

    # Record decision
    decision = item.to_dict()
    decision['action'] = action.value
    decision['reviewed_at'] = reviewed_at
    if audit_writer is not None:
        audit_writer.append(decision)
    else:
        append_jsonl('logs/review_actions.jsonl', decision)
    decision_store.append(decision)

    return action


# ── Modes ───────────────────────────────────────────────────────────
def run_console(cfg: dict):
    """One-shot or continuous console poll loop."""
    scoring = ScoringEngine(
        keywords=cfg.get('keywords', []),
        blocked_domains=cfg.get('blocked_domains', []),
        trusted_senders=cfg.get('trusted_senders', []),
    )
    pending_store = PendingStore()
    decision_store = DecisionStore()
    ignore_store = IgnoreStore()
    dedup = DedupCache(window_seconds=300)
    group_store = GroupStore()
    executor = DesktopWeChatKickExecutor(dry_run=cfg.get('dry_run', True))
    allowed_groups = cfg.get('allowed_groups', [])

    # Use rotating log writer for the audit trail
    audit_writer = RotatingJSONLWriter(
        'logs/review_actions.jsonl',
        max_bytes=cfg.get('log_max_bytes', 5 * 1024 * 1024),
        backup_count=cfg.get('log_backup_count', 5),
    )
    # Rotate any oversized existing log on startup
    rotate_logs('logs/review_actions.jsonl',
                max_bytes=cfg.get('log_max_bytes', 5 * 1024 * 1024),
                backup_count=cfg.get('log_backup_count', 5))

    watcher = make_watcher(cfg, group_store)
    poll_interval = cfg.get('poll_interval', 5.0)
    once = cfg.get('mock_once', False)

    logger.info('Starting console mode (interval=%.1fs, dry_run=%s)',
                poll_interval, cfg.get('dry_run', True))
    logger.info('Keywords: %s', cfg.get('keywords', []))

    while True:
        try:
            for msg in watcher.poll():
                process_message(
                    msg, scoring, pending_store, decision_store,
                    ignore_store, dedup, executor, allowed_groups, cfg,
                    audit_writer=audit_writer,
                )
        except Exception as e:
            logger.exception('Error during poll: %s', e)

        if once:
            break
        time.sleep(poll_interval)


def run_gui():
    """Launch the Tkinter review GUI."""
    from gui.app import main as gui_main
    gui_main()


# ── CLI ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='WeChat Group Guard')
    parser.add_argument('--mode', choices=['console', 'gui', 'mock'],
                        default='gui',
                        help='console=poll loop, gui=Tkinter panel (default), mock=one-shot demo')
    args = parser.parse_args()

    cfg = load_config()

    # Ensure data/logs directories exist
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)

    if args.mode == 'gui':
        run_gui()
    elif args.mode == 'mock':
        cfg['mock_once'] = True
        run_console(cfg)
    else:
        run_console(cfg)


if __name__ == '__main__':
    main()
