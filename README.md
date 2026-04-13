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
