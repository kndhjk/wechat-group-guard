# Architecture

## Flow

```
Watcher (mock or WeChat desktop)
  ↓ polls messages
ScoringEngine (keywords + rules + repeat-offender tracker)
  ↓ score ≥ 30?
  ├─ no  → log only
  └─ yes → pending_reviews.json + review prompt
              ├─ Approve Kick → executor.kick() (dry-run by default)
              ├─ Skip         → log skip
              └─ Ignore User  → ignored_users.json + skip future detection
           → reviewer_decisions.json (audit)
```

## Modules

| Module | Responsibility |
|--------|---------------|
| `watcher/windows_wechat.py` | UI Automation: enumerate groups, click group, read messages |
| `watcher/mock_file.py` | Demo: reads from `samples/mock_messages.json` once |
| `watcher/dedup.py` | Deduplicate (group, sender, text) within 5-min window |
| `watcher/filtering.py` | Group allowlist filter |
| `detector/rules.py` | Keyword/regex signal detection + domain blocklist |
| `detector/scoring.py` | Weighted scoring + repeat-offender tracker |
| `review/queue.py` | ReviewItem dataclass (pending/approved/skipped/ignored) |
| `review/console.py` | Console review prompt (k=kick, i=ignore, s=skip) |
| `storage/pending_store.py` | JSON file: pending review queue |
| `storage/decision_store.py` | JSON file: all review decisions |
| `storage/ignore_store.py` | JSON file: permanently ignored senders |
| `storage/group_store.py` | JSON file: monitored group list |
| `executor/desktop_stub.py` | UI Automation kick flow (dry_run=true by default) |
| `gui/app.py` | Tkinter GUI: table + actions + auto-refresh |
| `main.py` | CLI entry point; mode=gui/console/mock |

## Safety properties

- `dry_run=true` by default — no real kicks ever happen without changing config
- All actions logged to `logs/review_actions.jsonl` (append-only)
- Ignore list is permanent whitelist — a sender added there is never auto-removed
- `main.py --mode gui` does NOT start the watcher; it only runs the review panel
- The watcher loop (`--mode console`) runs independently of the GUI

## Running the watcher continuously

The polling loop is separate from the GUI to avoid UI blocking:

```bash
# Terminal 1: watcher loop (console mode)
python main.py --mode console

# Terminal 2: review GUI
python main.py --mode gui
```

Both read/write the same `data/pending_reviews.json` file.
