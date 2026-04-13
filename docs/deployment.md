# Deployment

## Quick install

```bash
git clone https://github.com/kndhjk/wechat-group-guard.git
cd wechat-group-guard
./scripts/install.sh
```

## Run GUI

```bash
./scripts/run.sh
```

## Current behavior

The current GUI is a local review console for pending items stored in:
- `data/pending_reviews.json`

Approved/skipped items are moved into:
- `data/reviewer_decisions.json`

## Uninstall

```bash
./scripts/uninstall.sh
```

This removes the Python virtual environment only.

If you also want a full delete:
- remove the whole project folder, or
- additionally delete `data/` and `logs/`
