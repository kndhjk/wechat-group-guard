import json
from pathlib import Path


class GroupStore:
    def __init__(self, path: str = 'data/groups.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def load(self) -> list[dict]:
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, groups: list[dict]) -> None:
        self.path.write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding='utf-8')
