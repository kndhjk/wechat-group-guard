# Product direction

## Core promise

A review-first moderation helper for ordinary WeChat groups.

The key differentiator vs. other moderation bots:
- **No auto-kick.** Detection surfaces suspicious messages; a human always decides.
- **Runs on your own desktop.** No server, no cloud, no WeChat API key needed.
- **Safe by default.** `dry_run=true` means the first run never makes mistakes you can't undo.

## Real target users

- Owners / admins of ordinary WeChat groups (< 500 members)
- Student groups, community groups, marketplace groups plagued by ad spam
- People who want to protect their groups without deploying a server or bot

## What "done" looks like

A non-technical user can:
1. Download a ZIP
2. Double-click `install.bat`
3. Double-click `run_gui.bat`
4. See their WeChat group list, pick groups to monitor
5. Start receiving review alerts with Approve / Skip / Ignore buttons
6. Click Approve → see the spammer get removed from the group

## Positioning

vs. **WeChat native features**: WeChat has no group management. This fills the gap.

vs. **Bot-based moderation** (e.g. Telegram bots): Bots require group admin rights and server hosting. This runs locally on your PC and reads the desktop UI — no special permissions needed.

vs. **auto-kick scripts**: A script that auto-kicks on keyword match will get it wrong. This makes every decision human-reviewed.

## Pricing

Free and open source. No server, no accounts, no data leaves your machine.

## Distribution

The primary distribution target is a **Windows EXE ZIP** that non-technical users can run without installing Python.
