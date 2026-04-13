import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

PENDING_PATH = Path('data/pending_reviews.json')
DECISION_PATH = Path('data/reviewer_decisions.json')


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


class ReviewApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('WeChat Group Guard')
        self.root.geometry('900x520')
        self.pending = []

        self.tree = ttk.Treeview(root, columns=('group', 'sender', 'reasons'), show='headings')
        self.tree.heading('group', text='Group')
        self.tree.heading('sender', text='Sender')
        self.tree.heading('reasons', text='Reasons')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(root, height=10)
        self.text.pack(fill=tk.BOTH, expand=False)

        btns = tk.Frame(root)
        btns.pack(fill=tk.X)
        tk.Button(btns, text='Refresh', command=self.refresh).pack(side=tk.LEFT)
        tk.Button(btns, text='Approve Kick', command=self.approve).pack(side=tk.LEFT)
        tk.Button(btns, text='Skip', command=self.skip).pack(side=tk.LEFT)

        self.tree.bind('<<TreeviewSelect>>', self.show_selected)
        self.refresh()

    def refresh(self):
        self.pending = load_json(PENDING_PATH, [])
        for row in self.tree.get_children():
            self.tree.delete(row)
        for idx, item in enumerate(self.pending):
            self.tree.insert('', tk.END, iid=str(idx), values=(item.get('group_name', ''), item.get('sender', ''), ', '.join(item.get('reasons', []))))
        self.text.delete('1.0', tk.END)

    def show_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self.pending[idx]
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, json.dumps(item, ensure_ascii=False, indent=2))

    def _record_decision(self, approved: bool):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a pending item first.')
            return
        idx = int(sel[0])
        item = self.pending.pop(idx)
        decisions = load_json(DECISION_PATH, [])
        item['approved'] = approved
        decisions.append(item)
        save_json(DECISION_PATH, decisions)
        save_json(PENDING_PATH, self.pending)
        self.refresh()

    def approve(self):
        self._record_decision(True)

    def skip(self):
        self._record_decision(False)


def main():
    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
