from __future__ import annotations

from typing import List

try:
    import uiautomation as auto
except Exception:  # pragma: no cover
    auto = None


class WeChatWindowProbe:
    def __init__(self, window_name: str = '微信'):
        self.window_name = window_name

    def get_window(self):
        if auto is None:
            raise RuntimeError('uiautomation is not installed')
        win = auto.WindowControl(searchDepth=1, Name=self.window_name)
        if not win.Exists(1):
            raise RuntimeError('WeChat main window not found')
        return win

    def list_conversation_names(self, limit: int = 100) -> List[str]:
        win = self.get_window()
        names: List[str] = []
        try:
            for ctrl in win.GetChildren():
                for child in ctrl.GetChildren():
                    name = getattr(child, 'Name', '') or ''
                    if name and name not in names:
                        names.append(name)
                        if len(names) >= limit:
                            return names
        except Exception:
            pass
        return names
