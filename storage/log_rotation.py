"""
Log rotation utilities for WeChat Group Guard.

Provides:
  - RotatingJSONLHandler: rotates review_actions.jsonl when it exceeds
    max_bytes, keeping backup_count rotated copies.
  - rotate_logs(): standalone function to rotate any file.
"""

from __future__ import annotations

import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_MAX_BYTES = 5 * 1024 * 1024   # 5 MB per log file
DEFAULT_BACKUP_COUNT = 5


def rotate_logs(
    log_path: str | Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> Optional[str]:
    """
    Rotate `log_path` if it exceeds `max_bytes`.

    Rotation scheme:
      log_path → log_path.1.gz → log_path.2.gz … → log_path.{backup_count}.gz
      Oldest backups beyond backup_count are deleted.

    Returns the reason for rotation, or None if no rotation needed.
    """
    p = Path(log_path)
    if not p.exists():
        return None

    size = p.stat().st_size
    if size < max_bytes:
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rotated_reason = f'size={size} > max_bytes={max_bytes}'

    # ── GZip-compress current file as .1.gz ─────────────────────────
    gz_path = p.with_suffix(f'.1.gz')
    with p.open('rb') as src, gzip.open(gz_path, 'wb', compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)

    # ── Shift existing backups ─────────────────────────────────────────
    for i in range(backup_count - 1, 0, -1):
        src_gz = p.with_suffix(f'.{i}.gz')
        dst_gz = p.with_suffix(f'.{i+1}.gz')
        if src_gz.exists():
            if dst_gz.exists():
                dst_gz.unlink()
            src_gz.rename(dst_gz)

    # ── Truncate current file ────────────────────────────────────────
    p.write_text('', encoding='utf-8')

    return rotated_reason


class RotatingJSONLWriter:
    """
    Appends JSONL records to `path`, automatically rotating when
    `max_bytes` is exceeded.

    Usage:
        writer = RotatingJSONLWriter('logs/review_actions.jsonl', max_bytes=5_000_000)
        writer.append({'action': 'kick', 'sender': 'Spammer'})
    """

    def __init__(
        self,
        path: str | Path,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def append(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False) + '\n'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('', encoding='utf-8')

        self.path.open('a', encoding='utf-8').write(line)
        self.path.chmod(0o644)

        # Check size and rotate if needed
        size = self.path.stat().st_size
        if size > self.max_bytes:
            rotate_logs(self.path, self.max_bytes, self.backup_count)
