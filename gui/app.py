"""
WeChat Group Guard — Tkinter GUI.

Features:
  - Color-coded score rows (🔴 60+, 🟡 30-59, ⚪ <30)
  - Auto-refresh every 5 seconds
  - Approve Kick / Skip / Ignore User actions
  - Manage ignored users (list + remove)
  - Group selection panel

Run:
  python main.py --mode gui
  # or
  python gui/app.py
"""

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

AUTO_REFRESH_MS = 5000   # 5 seconds


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


class ReviewApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('WeChat Group Guard')
        self.root.geometry('1200x720')
        self.root.minsize(900, 500)

        self.pending: list[dict] = []
        self.group_store = GroupStore(str(GROUPS_PATH))
        self.ignore_store = IgnoreStore()
        self.group_vars: dict[str, tk.BooleanVar] = {}
        self._auto_refresh_job: str | None = None

        self._build_ui()
        self._schedule_refresh()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────
        top = tk.Frame(self.root, bg='#2c3e50', pady=6)
        top.pack(fill=tk.X)

        tk.Label(
            top, text='WeChat Group Guard',
            font=('Arial', 15, 'bold'), fg='white', bg='#2c3e50'
        ).pack(side=tk.LEFT, padx=12)

        status_frame = tk.Frame(top, bg='#2c3e50')
        status_frame.pack(side=tk.RIGHT, padx=12)
        self.status_label = tk.Label(
            status_frame, text='Loading…',
            font=('Arial', 9), fg='#bdc3c7', bg='#2c3e50'
        )
        self.status_label.pack()
        tk.Button(
            top, text='⏹ Stop Auto-Refresh',
            command=self._stop_auto_refresh,
            font=('Arial', 9), cursor='hand2'
        ).pack(side=tk.RIGHT, padx=8)

        # ── Main area ──────────────────────────────────────────────
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        # Left sidebar: groups + legend
        left = tk.Frame(main, width=230, bg='#f8f9fa')
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        self._build_sidebar(left)

        # Right: table + detail + actions
        right = tk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_review_panel(right)

    def _build_sidebar(self, parent):
        tk.Label(parent, text='Monitored Groups',
                 font=('Arial', 10, 'bold'), bg='#f8f9fa', anchor='w').pack(
            fill=tk.X, padx=10, pady=(10, 4))

        self.group_frame = tk.Frame(parent, bg='#f8f9fa')
        self.group_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Button(parent, text='💾 Save Group Selection',
                  command=self.save_groups,
                  font=('Arial', 9), cursor='hand2').pack(fill=tk.X, padx=10, pady=(0, 4))

        tk.Button(parent, text='🔄 Refresh Groups',
                  command=self.load_groups,
                  font=('Arial', 9), cursor='hand2').pack(fill=tk.X, padx=10)

        sep = tk.Frame(parent, height=1, bg='#cccccc')
        sep.pack(fill=tk.X, padx=10, pady=12)

        tk.Label(parent, text='Score Legend',
                 font=('Arial', 9, 'bold'), bg='#f8f9fa', anchor='w').pack(
            fill=tk.X, padx=10, pady=(0, 4))
        for label, bg, fg in [
            ('🔴 High  60–100', '#ffcccc', '#c0392b'),
            ('🟡 Mid   30–59',   '#fff3cd', '#856404'),
            ('⚪ Low   0–29',    '#f8f8f8', '#333333'),
        ]:
            tk.Label(parent, text=label, bg=bg, fg=fg,
                     font=('Arial', 9), anchor='w',
                     padx=6, pady=2).pack(fill=tk.X, padx=10, pady=1)

        sep2 = tk.Frame(parent, height=1, bg='#cccccc')
        sep2.pack(fill=tk.X, padx=10, pady=12)

        tk.Button(parent, text='🚫 Manage Ignored Users',
                 command=self.manage_ignored,
                 font=('Arial', 9), cursor='hand2').pack(fill=tk.X, padx=10)

    def _build_review_panel(self, parent):
        # Toolbar
        toolbar = tk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 4))

        tk.Label(toolbar, text='Pending Reviews',
                 font=('Arial', 11, 'bold')).pack(side=tk.LEFT)

        right = tk.Frame(toolbar)
        right.pack(side=tk.RIGHT)
        tk.Button(right, text='🔄 Refresh Now',
                  command=self.refresh,
                  font=('Arial', 9), cursor='hand2').pack(side=tk.LEFT, padx=4)

        # Table
        table_frame = tk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('group', 'sender', 'score', 'reasons')
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show='headings',
            selectmode='browse', height=12
        )
        col_widths = {'group': 180, 'sender': 140, 'score': 65, 'reasons': 380}
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=col_widths.get(col, 120), anchor='w')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Row tags for colors
        self.tree.tag_configure('high', background='#ffcccc')
        self.tree.tag_configure('mid',  background='#fff3cd')
        self.tree.tag_configure('low',  background='#f8f8f8')
        self.tree.tag_configure('high_sel', background='#e74c3c')
        self.tree.tag_configure('mid_sel',  background='#f39c12')
        self.tree.tag_configure('low_sel',  background='#bdc3c7')

        # Detail text
        self.detail = tk.Text(parent, height=9, font=('Courier', 9), wrap='word')
        self.detail.pack(fill=tk.BOTH, expand=False, pady=(4, 0))

        # Action buttons
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(6, 0))

        tk.Button(
            btn_frame, text='✅ Approve Kick',
            command=self.approve, bg='#27ae60', fg='white',
            activebackground='#1e8449', font=('Arial', 11, 'bold'),
            cursor='hand2', padx=10,
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btn_frame, text='⏭ Skip',
            command=self.skip, bg='#95a5a6', fg='white',
            activebackground='#7f8c8d', font=('Arial', 10),
            cursor='hand2', padx=10,
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btn_frame, text='👤 Ignore User',
            command=self.ignore_user, bg='#f39c12', fg='white',
            activebackground='#d68910', font=('Arial', 10),
            cursor='hand2', padx=10,
        ).pack(side=tk.LEFT, padx=6)

        tk.Label(
            btn_frame,
            text='⚠️ Dry-run mode: kick actions are simulated until config dry_run=false',
            fg='#e67e22', font=('Arial', 8), anchor='e'
        ).pack(side=tk.RIGHT, padx=8)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    # ── Refresh logic ───────────────────────────────────────────────

    def _schedule_refresh(self):
        self.refresh()
        self._auto_refresh_job = self.root.after(AUTO_REFRESH_MS, self._schedule_refresh)

    def _stop_auto_refresh(self):
        if self._auto_refresh_job:
            self.root.after_cancel(self._auto_refresh_job)
            self._auto_refresh_job = None
            self.status_label.config(text='⏹ Auto-refresh stopped')
        else:
            self._schedule_refresh()
            self.status_label.config(text=f'🔄 Auto-refresh every {AUTO_REFRESH_MS/1000:.0f}s')

    def refresh(self):
        self.pending = load_json(PENDING_PATH, [])
        # Clear table
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Repopulate
        for idx, item in enumerate(self.pending):
            score = item.get('score', 0)
            tag = 'high' if score >= 60 else 'mid' if score >= 30 else 'low'
            reasons_str = ', '.join(item.get('reasons', []))
            self.tree.insert('', tk.END, iid=str(idx), values=(
                item.get('group_name', ''),
                item.get('sender', ''),
                f'{score}/100',
                reasons_str[:100] + ('…' if len(reasons_str) > 100 else ''),
            ), tags=(tag,))
        self.detail.delete('1.0', tk.END)
        self.status_label.config(
            text=f'🔄 {len(self.pending)} pending · refreshed {self._now()}'
        )

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.detail.delete('1.0', tk.END)
            return
        idx = int(sel[0])
        if idx >= len(self.pending):
            return
        item = self.pending[idx]
        text = json.dumps(item, ensure_ascii=False, indent=2)
        self.detail.delete('1.0', tk.END)
        self.detail.insert('1.0', text)

    # ── Actions ─────────────────────────────────────────────────────

    def _record_decision(self, approved: bool, ignore_user: bool = False):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a pending item first.')
            return False
        idx = int(sel[0])
        item = self.pending.pop(idx)

        if ignore_user:
            sender = item.get('sender', '')
            reason = item.get('reason', '') or 'ignored_from_gui'
            review_id = item.get('review_id', '')
            self.ignore_store.add(sender, reason=reason, review_id=review_id)
            item['status'] = 'ignored'
            logger.info('Ignored user: %s', sender)
        else:
            item['status'] = 'approved' if approved else 'skipped'
            item['approved'] = approved

        decisions = load_json(DECISION_PATH, [])
        decisions.append(item)
        save_json(DECISION_PATH, decisions)
        save_json(PENDING_PATH, self.pending)
        self.refresh()
        return True

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
        if messagebox.askyesno(
            'Confirm Ignore',
            f"Ignore all messages from [{sender}]?\n\n"
            f"They will be permanently whitelisted and skip detection.",
        ):
            self._record_decision(False, ignore_user=True)

    # ── Group management ────────────────────────────────────────────

    def load_groups(self):
        for child in self.group_frame.winfo_children():
            child.destroy()
        self.group_vars.clear()
        for item in self.group_store.load():
            var = tk.BooleanVar(value=item.get('enabled', False))
            self.group_vars[item['name']] = var
            tk.Checkbutton(
                self.group_frame, text=item['name'],
                variable=var, anchor='w', bg='#f8f9fa',
                font=('Arial', 9),
            ).pack(fill=tk.X)

    def save_groups(self):
        groups = [
            {'name': name, 'enabled': var.get()}
            for name, var in self.group_vars.items()
        ]
        self.group_store.save(groups)
        messagebox.showinfo('Saved', f'Group selection saved ({len(groups)} groups).')

    # ── Ignored users dialog ────────────────────────────────────────

    def manage_ignored(self):
        win = tk.Toplevel(self.root)
        win.title('Ignored Users')
        win.geometry('600x450')
        win.transient(self.root)

        tk.Label(win, text='Permanently Ignored Users',
                 font=('Arial', 12, 'bold')).pack(anchor='w', padx=12, pady=8)

        list_frame = tk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        scroll_y = ttk.Scrollbar(list_frame, orient='vertical')
        scroll_y.pack(side='right', fill='y')
        scroll_x = ttk.Scrollbar(list_frame, orient='horizontal')
        scroll_x.pack(side='bottom', fill='x')

        listbox = tk.Listbox(
            list_frame, font=('Courier', 10),
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        listbox.pack(side='left', fill='both', expand=True)
        scroll_y.config(command=listbox.yview)
        scroll_x.config(command=listbox.xview)

        ignored = self.ignore_store.load()
        for u in ignored:
            date = u.ignored_at[:10] if u.ignored_at else '?'
            label = f'{u.sender:<25} reason={u.reason or "-":<20} since={date}'
            listbox.insert(tk.END, label)

        bottom = tk.Frame(win)
        bottom.pack(pady=8)

        def remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            sender = ignored[sel[0]].sender
            self.ignore_store.remove(sender)
            messagebox.showinfo('Removed', f'{sender} removed from ignore list.')
            win.destroy()
            self.manage_ignored()

        tk.Button(bottom, text='❌ Remove Selected',
                 command=remove_selected, font=('Arial', 10),
                 bg='#e74c3c', fg='white', cursor='hand2').pack(side=tk.LEFT, padx=8)
        tk.Button(bottom, text='Close',
                 command=win.destroy, font=('Arial', 10)).pack(side=tk.LEFT, padx=8)

    # ── Utilities ────────────────────────────────────────────────────
    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S')


# Module-level logger for gui actions
import logging
logger = logging.getLogger('wcg.gui')


def main():
    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
