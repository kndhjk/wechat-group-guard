import json
from pathlib import Path
from typing import Any


class DecisionStore:
    def __init__(self, path: str = 'data/reviewer_decisions.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def append(self, item: dict[str, Any]) -> None:
        data = json.loads(self.path.read_text(encoding='utf-8'))
        data.append(item)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def load(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding='utf-8'))
