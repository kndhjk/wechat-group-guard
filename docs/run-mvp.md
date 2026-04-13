# Run MVP locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Current MVP uses mock messages and console review.

Files created while running:
- `data/messages.jsonl`
- `data/pending_reviews.json`
- `logs/review_actions.jsonl`
