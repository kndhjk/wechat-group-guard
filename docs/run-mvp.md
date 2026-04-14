# Run the project

## Windows (recommended for real WeChat use)

```bat
# First-time install
scripts\install.bat

# Edit config.yaml before running!

# Run GUI (default)
scripts\run_gui.bat

# Run console polling mode
python main.py --mode console

# Probe WeChat conversation names
scripts\probe_wechat_groups.bat
```

## Linux / macOS / Git Bash (demo/mock only)

WeChat desktop is Windows-only, so Linux/macOS can only run mock mode.

```bash
# Install
./scripts/install.sh

# Run GUI (mock)
./scripts/run.sh

# Run one-shot mock demo
python main.py --mode mock

# Run continuous console poll (mock)
python main.py --mode console
```

## Build EXE (Windows only)

```bat
scripts\install.bat
scripts\build_exe.bat
```

Requires: Python 3.10+ on Windows, `pyinstaller` installed.

## Run tests

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --tb=short
```

## Log rotation

`logs/review_actions.jsonl` is auto-rotated when it exceeds 5 MB:
- Rotated files are gzip-compressed: `review_actions.jsonl.1.gz`, `.2.gz` …
- Up to 5 backups are kept (configurable via `config.yaml`).
- To manually trigger rotation:
  ```python
  from storage.log_rotation import rotate_logs
  rotate_logs('logs/review_actions.jsonl')
  ```

## Config

Copy `config.example.yaml` → `config.yaml` and edit:

```yaml
dry_run: true          # ← set to false ONLY after testing
allowed_groups: []     # [] = all groups
poll_interval: 5       # seconds
keywords: [...]
```

## Data directories

Created automatically on first run:

```
data/
  pending_reviews.json     ← GUI review queue
  reviewer_decisions.json  ← all decisions
  ignored_users.json       ← whitelist
  messages.jsonl            ← all scanned messages
logs/
  review_actions.jsonl     ← audit log (append-only)
```
