# Windows implementation plan

## Why Windows first
Desktop WeChat automation is most practical on Windows because UI Automation tooling is better established.

## Candidate stack
- Python
- pywinauto / uiautomation
- optional OCR fallback

## Watcher idea
1. Find WeChat main window
2. Switch to whitelisted group chat
3. Read visible message list items
4. De-duplicate by sender + text + time
5. Feed suspicious messages into review queue

## Kick executor idea
1. Confirm reviewer approval exists
2. Focus target group window
3. Open group member list or message context menu
4. Locate sender entry
5. Trigger remove action
6. Write audit log

## Important constraint
The project is review-first and should never auto-kick without explicit approval.
