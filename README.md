# WeChat Group Guard

Desktop WeChat moderation assistant for ordinary WeChat groups.

## Goal

Monitor selected WeChat group chats from the desktop client, detect likely ads/spam, send them for human review, and only kick after approval.

## MVP scope

- Watch selected groups on desktop WeChat
- Detect likely ad/spam text using rules
- Queue suspicious messages for review
- Require explicit approval before kick
- Keep action/audit logs

## Planned architecture

- `watcher/` - read new messages from desktop WeChat UI
- `detector/` - rule-based ad/spam detection
- `review/` - approval workflow
- `executor/` - UI automation to kick after approval
- `storage/` - logs, queue, config

## Safety model

This project is review-first:
- detection does **not** auto-kick
- human approval is required before group action
- all actions should be logged

## Status

Initial scaffold in progress.

## Current implementation status

Implemented now:
- mock watcher
- rule detector
- console review flow
- audit logging
- desktop watcher stub
- desktop kick executor stub

Planned next:
- real desktop WeChat integration on Windows
- persistent review queue
- whitelist of monitored groups

## GUI

A simple local desktop review GUI is included in this repo.

## Install / run / uninstall

Quick install:

```bash
./scripts/install.sh
```

Run GUI:

```bash
./scripts/run.sh
```

Uninstall virtualenv only:

```bash
./scripts/uninstall.sh
```

More detail:
- `docs/deployment.md`

## EXE packaging

Planned Windows packaging is included via PyInstaller.
See: `docs/windows-build.md`
