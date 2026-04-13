import json
from pathlib import Path
from typing import Any


class PendingStore:
    def __init__(self, path: str = 'data/pending_reviews.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def load(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, items: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

    def add(self, item: dict[str, Any]) -> None:
        items = self.load()
        items.append(item)
        self.save(items)
