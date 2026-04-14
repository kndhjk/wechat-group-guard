from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from storage.group_store import GroupStore
from storage.ignore_store import IgnoreStore


PENDING_PATH = Path('data/pending_reviews.json')
DECISION_PATH = Path('data/reviewer_decisions.json')
GROUPS_PATH = Path('samples/groups.json')
IGNORED_PATH = Path('data/ignored_users.json')


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
        self.root.geometry('1200x680')

        self.pending = []
        self.group_store = GroupStore(str(GROUPS_PATH))
        self.ignore_store = IgnoreStore()
        self.group_vars = {}

        self._build_ui()
        self.load_groups()
        self.refresh()

    def _build_ui(self):
        # ── Top toolbar ──────────────────────────────────────────────
        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(toolbar, text='WeChat Group Guard', font=('Arial', 14, 'bold')).pack(side=tk.LEFT)

        right_tools = tk.Frame(toolbar)
        right_tools.pack(side=tk.RIGHT)
        tk.Button(right_tools, text='Manage Ignored Users', command=self.manage_ignored).pack(side=tk.LEFT, padx=4)
        tk.Button(right_tools, text='Refresh', command=self.refresh).pack(side=tk.LEFT, padx=4)

        # ── Main area ───────────────────────────────────────────────
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left panel: group selection
        left = tk.Frame(main, width=240)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        tk.Label(left, text='Monitored Groups', font=('Arial', 10, 'bold')).pack(anchor='w')
        self.group_frame = tk.Frame(left)
        self.group_frame.pack(fill=tk.X, pady=6)
        tk.Button(left, text='Save Selection', command=self.save_groups).pack(fill=tk.X, pady=(0, 4))

        sep = tk.Frame(left, height=1, bg='#cccccc')
        sep.pack(fill=tk.X, pady=8)

        tk.Label(left, text='Legend', font=('Arial', 9, 'bold')).pack(anchor='w')
        legend_items = [
            ('🔴 Score 60+', '#ffcccc'),
            ('🟡 Score 30-59', '#fff3cd'),
            ('⚪ Non-suspicious', '#f8f8f8'),
        ]
        for label, bg in legend_items:
            tk.Label(left, text=label, bg=bg, font=('Arial', 9), anchor='w').pack(fill=tk.X, pady=1)

        # Right panel: review list + detail
        right = tk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Table
        cols = ('group', 'sender', 'score', 'reasons')
        self.tree = ttk.Treeview(right, columns=cols, show='headings', selectmode='browse')
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
        self.tree.column('group', width=180)
        self.tree.column('sender', width=140)
        self.tree.column('score', width=60)
        self.tree.column('reasons', width=320)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Row tag colors
        self.tree.tag_configure('high', background='#ffcccc')
        self.tree.tag_configure('mid', background='#fff3cd')
        self.tree.tag_configure('low', background='#f8f8f8')

        # Detail text
        self.detail = tk.Text(right, height=8, font=('Courier', 9), wrap='word')
        self.detail.pack(fill=tk.BOTH, expand=False, pady=(4, 0))

        # Action buttons
        btns = tk.Frame(right)
        btns.pack(fill=tk.X, pady=4)
        tk.Button(btns, text='✅ Approve Kick', command=self.approve, bg='#d4edda',
                  activebackground='#c3e6cb', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text='🚫 Skip', command=self.skip,
                  font=('Arial', 10)).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text='👤 Ignore User', command=self.ignore_user, bg='#fff3cd',
                  activebackground='#ffeeba', font=('Arial', 10)).pack(side=tk.LEFT, padx=4)

        self.tree.bind('<<TreeviewSelect>>', self.show_selected)

    def load_groups(self):
        for child in self.group_frame.winfo_children():
            child.destroy()
        self.group_vars = {}
        for item in self.group_store.load():
            var = tk.BooleanVar(value=item.get('enabled', False))
            self.group_vars[item['name']] = var
            tk.Checkbutton(self.group_frame, text=item['name'], variable=var, anchor='w').pack(fill=tk.X)

    def save_groups(self):
        groups = [{'name': name, 'enabled': var.get()} for name, var in self.group_vars.items()]
        self.group_store.save(groups)
        messagebox.showinfo('Saved', 'Group selection saved.')

    def refresh(self):
        self.pending = load_json(PENDING_PATH, [])
        for row in self.tree.get_children():
            self.tree.delete(row)
        for idx, item in enumerate(self.pending):
            score = item.get('score', 0)
            reasons = ', '.join(item.get('reasons', []))
            tag = 'high' if score >= 60 else 'mid' if score >= 30 else 'low'
            self.tree.insert('', tk.END, iid=str(idx), values=(
                item.get('group_name', ''),
                item.get('sender', ''),
                f'{score}/100',
                reasons[:80] + ('…' if len(reasons) > 80 else ''),
            ), tags=(tag,))
        self.detail.delete('1.0', tk.END)

    def show_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self.pending[idx]
        self.detail.delete('1.0', tk.END)
        text = json.dumps(item, ensure_ascii=False, indent=2)
        self.detail.insert('1.0', text)

    def _record_decision(self, approved: bool, ignore_user: bool = False):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a pending item first.')
            return
        idx = int(sel[0])
        item = self.pending.pop(idx)

        if ignore_user:
            reason = 'ignored_from_gui'
            review_id = item.get('review_id', '')
            self.ignore_store.add(item.get('sender', ''), reason=reason, review_id=review_id)
            item['status'] = 'ignored'
        else:
            item['status'] = 'approved' if approved else 'skipped'
            item['approved'] = approved

        decisions = load_json(DECISION_PATH, [])
        decisions.append(item)
        save_json(DECISION_PATH, decisions)
        save_json(PENDING_PATH, self.pending)
        self.refresh()

    def approve(self):
        self._record_decision(True)

    def skip(self):
        self._record_decision(False)

    def ignore_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a pending item first.')
            return
        idx = int(sel[0])
        item = self.pending[idx]
        sender = item.get('sender', '')
        confirm = messagebox.askyesno(
            'Confirm Ignore',
            f"Ignore all messages from [{sender}]?\nThey will be whitelisted and skip detection.",
        )
        if confirm:
            self._record_decision(False, ignore_user=True)

    def manage_ignored(self):
        """Open a window listing all ignored users with remove option."""
        win = tk.Toplevel(self.root)
        win.title('Ignored Users')
        win.geometry('500x400')

        ignored = self.ignore_store.load()

        list_frame = tk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(list_frame, font=('Courier', 10), yscrollcommand=scroll.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=listbox.yview)

        for u in ignored:
            label = f"{u.sender}  (ignored {u.ignored_at[:10] if u.ignored_at else '?'}, reason: {u.reason or '-'})"
            listbox.insert(tk.END, label)

        def remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            sender = ignored[sel[0]].sender
            self.ignore_store.remove(sender)
            messagebox.showinfo('Removed', f'{sender} removed from ignore list.')
            win.destroy()
            self.manage_ignored()  # Refresh

        tk.Button(win, text='Remove Selected', command=remove_selected).pack(pady=4)
        tk.Button(win, text='Close', command=win.destroy).pack(pady=4)


def main():
    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
