# Windows Integration Guide

## Overview

The project uses **UI Automation** (Microsoft's native accessibility API) to read
messages from the WeChat desktop client and perform kick actions.

Stack: `uiautomation` (Python wrapper around UI Automation) + `pywinauto` as fallback.

## How it works

### Reading messages

1. Find the WeChat main window (`WindowControl Name='微信'`)
2. Walk the control tree to locate the conversation list (left pane)
3. Click the target group chat
4. Wait for the chat to load
5. Walk the message list control, extract sender name + message text
6. Return `ChatMessage(group_name, sender, text, timestamp)`

### Kick flow

1. Open the target group chat
2. Click the "N人" member count button → member list slides in
3. Search for the target member's name
4. Right-click → "Remove from group"
5. Confirm in the dialog
6. Log the outcome

## Requirements

- Windows 10/11
- WeChat desktop for Windows (tested with 3.x)
- Python 3.10+
- `pip install uiautomation` (included in requirements.txt)

## Testing UI element names

Use the **Inspect** tool (built into Windows) or **Accessibility Insights** to
see the actual control names and types in the WeChat window:

```
inspect.exe
```

Look for:
- `Name='微信'` on the main window
- `Name='聊天'` on the conversation list container
- Individual `ListItemControl` with `Name=<contact/group name>`
- Message area: `DocumentControl` or `RichEditControl`

## Known challenges

| Challenge | Mitigation |
|-----------|------------|
| WeChat updates change control names | Version-specific selectors; log warning if group not found |
| Group name with spaces | Exact string match in click target |
| Member not found (they left) | Graceful error: log + skip kick |
| Multi-instance WeChat | Target the first main window found |
| WeChat not installed | `is_available()` check before starting watcher |

## dry_run mode

The executor defaults to `dry_run=True` (safe mode). Set `dry_run: false` in
`config.yaml` only after confirming the watcher can read your groups correctly.

## Probe script

Before running the full watcher, test that WeChat is readable:

```bat
scripts\probe_wechat_groups.bat
```

This prints all conversation names WeChat UI Automation can see.
