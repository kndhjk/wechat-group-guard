import json
from pathlib import Path


class IgnoreStore:
    def __init__(self, path: str = 'data/ignored_users.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def load(self) -> list[str]:
        return json.loads(self.path.read_text(encoding='utf-8'))

    def contains(self, sender: str) -> bool:
        return sender in self.load()

    def add(self, sender: str) -> None:
        items = self.load()
        if sender not in items:
            items.append(sender)
            self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
