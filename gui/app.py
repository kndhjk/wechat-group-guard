import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from storage.group_store import GroupStore

PENDING_PATH = Path('data/pending_reviews.json')
DECISION_PATH = Path('data/reviewer_decisions.json')
GROUPS_PATH = Path('samples/groups.json')


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
        self.root.geometry('1100x620')
        self.pending = []
        self.group_store = GroupStore(str(GROUPS_PATH))
        self.group_vars = {}

        top = tk.Frame(root)
        top.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(top, width=260)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = tk.Frame(top)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text='Managed Groups').pack(anchor='w')
        self.group_frame = tk.Frame(left)
        self.group_frame.pack(fill=tk.X, pady=8)
        tk.Button(left, text='Save Group Selection', command=self.save_groups).pack(fill=tk.X)
        tk.Button(left, text='Refresh Groups', command=self.load_groups).pack(fill=tk.X)

        self.tree = ttk.Treeview(right, columns=('group', 'sender', 'reasons'), show='headings')
        self.tree.heading('group', text='Group')
        self.tree.heading('sender', text='Sender')
        self.tree.heading('reasons', text='Reasons')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(right, height=10)
        self.text.pack(fill=tk.BOTH, expand=False)

        btns = tk.Frame(right)
        btns.pack(fill=tk.X)
        tk.Button(btns, text='Refresh Pending', command=self.refresh).pack(side=tk.LEFT)
        tk.Button(btns, text='Approve Kick', command=self.approve).pack(side=tk.LEFT)
        tk.Button(btns, text='Skip', command=self.skip).pack(side=tk.LEFT)

        self.tree.bind('<<TreeviewSelect>>', self.show_selected)
        self.load_groups()
        self.refresh()

    def load_groups(self):
        for child in self.group_frame.winfo_children():
            child.destroy()
        self.group_vars = {}
        for item in self.group_store.load():
            var = tk.BooleanVar(value=item.get('enabled', False))
            self.group_vars[item['name']] = var
            tk.Checkbutton(self.group_frame, text=item['name'], variable=var).pack(anchor='w')

    def save_groups(self):
        groups = [{'name': name, 'enabled': var.get()} for name, var in self.group_vars.items()]
        self.group_store.save(groups)
        messagebox.showinfo('Saved', 'Group selection saved.')

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
