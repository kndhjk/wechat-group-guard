# WeChat Group Guard

Desktop WeChat moderation assistant for ordinary WeChat groups.

## Goal

Monitor selected WeChat group chats from the desktop client, detect likely ad/spam,
send them for human review, and only kick after approval. **Never auto-kicks.**

## Features

- **Review-first safety model** — detection never auto-kicks; human approves every action
- **Rule-based scoring** — keyword hits, URLs, phone numbers, blocked domains, disguised chars, repeat offenders
- **Ignore / whitelist users** — mark trusted senders to skip detection entirely
- **Time-window dedup** — 5-minute dedup window prevents duplicate reviews of the same message
- **Repeat offender tracking** — +20 score bonus for senders with ≥3 flagged messages in 24 h
- **GUI review panel** — Tkinter app with color-coded score rows and action buttons
- **Audit logging** — all messages and decisions written to append-only JSONL logs
- **Configurable** — keywords, blocked domains, trusted senders via `config.yaml`

## Architecture

```
watcher/       → poll new messages (mock or real Windows WeChat)
detector/      → rule-based scoring + repeat-offender tracking
review/        → queue + console/GUI review workflow
executor/      → desktop UI automation stub (real kick TBD)
storage/       → pending queue, decision log, ignore list, group config
```

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Run GUI
python gui/app.py

# Run console mode (demo with mock messages)
python main.py
```

## Config

Create `config.yaml` to customise:

```yaml
keywords:
  - 加V
  - 兼职
  - 刷单
  - 推广

allowed_groups:
  - 我的微信群

blocked_domains:
  - t.cn
  - bit.ly

trusted_senders:
  - GroupAdmin
```

## Safety model

- Detection does **not** auto-kick
- Human approval is required before any group action
- All actions are logged (append-only JSONL)

## Status

MVP scaffold complete. Real Windows desktop WeChat integration (UI reading + kick automation) is the main remaining work.
