# Review flow

## Supported actions

| Action | Shortcut | Effect |
|--------|----------|--------|
| Approve Kick | `k` | Record approval; hand off to executor for removal |
| Skip | `s` | Record skip; no action taken |
| Ignore User | `i` | Add sender to permanent whitelist; skip all future detection |

## Flow

1. Watcher yields new message
2. IgnoreStore check — skip if sender is whitelisted
3. DedupCache check — skip if (group, sender, text, 5-min window) is duplicate
4. ScoringEngine scores text; records repeat offender if applicable
5. Non-suspicious → logged only, no review item
6. Suspicious → item added to `data/pending_reviews.json`; review prompt shown
7. Reviewer chooses action → decision written to `logs/review_actions.jsonl`
8. GUI mirrors this flow with a visual table + action buttons

## Persistent review items

Each item carries:
- `review_id` (SHA1 of sender+text, first 12 hex chars)
- `timestamp`
- `score`
- `reasons[]`
- `status`: `pending` | `approved` | `skipped` | `ignored`

## Data files

- `data/pending_reviews.json` — queue for GUI consumption
- `logs/review_actions.jsonl` — append-only audit log
- `data/ignored_users.json` — whitelist (sender + reason + timestamp)
- `data/reviewer_decisions.json` — all decisions (GUI export)
