"""
Real Windows WeChat watcher via UI Automation (uiautomation / pywinauto).

Architecture:
  WeChatWindowProbe  — enumerate conversation names
  WeChatMessageReader — read messages from a specific group chat
  WeChatWatcher      — orchestrates probe + reader, yields ChatMessage continuously

Requirements (Windows only):
  pip install uiautomation

Usage:
  from watcher.windows_wechat import WeChatWatcher
  watcher = WeChatWatcher(groups=['我的群', '同学群'])
  for msg in watcher.poll():
      print(msg.group_name, msg.sender, msg.text)
"""

from __future__ import annotations

import time
import hashlib
from datetime import datetime
from typing import Iterable, Optional

from .base import MessageWatcher
from .models import ChatMessage


# ── uiautomation import (Windows only) ──────────────────────────────
try:
    import uiautomation as auto
    _HAS_AUTO = True
except ImportError:
    auto = None
    _HAS_AUTO = False
# ───────────────────────────────────────────────────────────────────


# Well-known WeChat window and control names (localised)
_CHAT_LIST_NAME = '聊天'
_MEMBER_LIST_NAME = '成员'
_WECHAT_WINDOW = 'Weixin'


def _get_wechat_window() -> auto.WindowControl:
    if not _HAS_AUTO:
        raise RuntimeError('uiautomation is not installed. Run: pip install uiautomation')
    win = auto.WindowControl(searchDepth=1, Name=_WECHAT_WINDOW)
    if not win.Exists(3):
        raise RuntimeError('WeChat window not found. Is WeChat desktop running?')
    return win


def _get_chat_list_control(win: auto.WindowControl) -> Optional[auto.Control]:
    """
    Navigate into the chat list pane.
    WeChat 3.x uses a TreeControl for the conversation list.
    """
    # Try the most common pattern: a ListControl or ListItemControl
    for ctrl in win.GetChildren():
        name = getattr(ctrl, 'Name', '') or ''
        ct = getattr(ctrl, 'ControlType', None)
        ct_name = str(ct) if ct is not None else ''
        if ct_name and 'List' in ct_name:
            return ctrl
        # Fallback: look for the "聊天" pane
        if name == _CHAT_LIST_NAME:
            return ctrl
    return None


def _get_message_list_control(win: auto.WindowControl) -> Optional[auto.Control]:
    """
    Find the message list inside a chat window.
    Usually a RichEdit or DocumentControl.
    """
    # The message area is typically the central pane
    for ctrl in win.GetChildren():
        name = getattr(ctrl, 'Name', '') or ''
        control_type = str(getattr(ctrl, 'ControlType', '')) or ''
        # Look for a document or rich-edit-like control in the chat area
        if 'Document' in control_type or 'Edit' in control_type:
            return ctrl
    return None


class WeChatWindowProbe:
    """Enumerate WeChat conversation names."""

    def __init__(self, window_name: str = _WECHAT_WINDOW):
        self.window_name = window_name

    def is_available(self) -> bool:
        """Check whether WeChat desktop is running."""
        if not _HAS_AUTO:
            return False
        win = auto.WindowControl(searchDepth=1, Name=self.window_name)
        return win.Exists(1)

    def list_conversation_names(self, limit: int = 200) -> list[str]:
        """
        Return the visible conversation names from the chat list.
        These include both private chats and group chats.
        """
        if not _HAS_AUTO:
            raise RuntimeError('uiautomation not available')
        win = _get_wechat_window()
        chat_list = _get_chat_list_control(win)
        names: list[str] = []
        if chat_list is None:
            return names
        try:
            for ctrl in chat_list.GetChildren():
                name: str = getattr(ctrl, 'Name', '') or ''
                if name and name not in names and name != _CHAT_LIST_NAME:
                    names.append(name)
                    if len(names) >= limit:
                        break
        except Exception:
            pass
        return names


class WeChatMessageReader:
    """
    Read the most recent messages from an open WeChat group chat.

    The caller is responsible for opening the correct chat first
    (e.g. via WeChatWindowProbe + clicking the group name).
    """

    # Known sender label patterns in the message list
    _SENDER_RE = None  # resolved at import time

    @classmethod
    def _sender_re(cls):
        # Lazy-compile to avoid import overhead at module load
        if cls._SENDER_RE is None:
            import re
            # WeChat shows sender names above each message bubble
            cls._SENDER_RE = re.compile(r'^(.{1,20}):', re.MULTILINE)
        return cls._SENDER_RE

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages

    def read_messages(self, group_name: str = '') -> list[ChatMessage]:
        """
        Read the most recent messages visible in the open chat window.
        Returns up to `max_messages` ChatMessage objects.
        """
        if not _HAS_AUTO:
            return []
        win = _get_wechat_window()
        msg_ctrl = _get_message_list_control(win)
        messages: list[ChatMessage] = []
        if msg_ctrl is None:
            return []
        try:
            children = msg_ctrl.GetChildren()
            # Walk through visible elements, extract sender + text
            buffer: list[str] = []
            current_sender = ''
            for child in children[-self.max_messages:]:
                name: str = getattr(child, 'Name', '') or ''
                if not name or name.isspace():
                    continue
                # heuristic: names that look like "UserName:" are sender labels
                # everything else is message body or part of it
                stripped = name.strip()
                if self._is_sender_label(stripped):
                    current_sender = stripped.rstrip(':')
                elif current_sender:
                    # This is a message body from current_sender
                    messages.append(ChatMessage(
                        group_name=group_name,
                        sender=current_sender,
                        text=stripped,
                        timestamp=datetime.now(),
                    ))
                    current_sender = ''
        except Exception:
            pass
        return messages

    @staticmethod
    def _is_sender_label(text: str) -> bool:
        """Heuristic: sender labels are short, don't contain spaces, end with :"""
        if not text.endswith(':'):
            return False
        bare = text[:-1]
        return 1 <= len(bare) <= 20 and ' ' not in bare


class WeChatWatcher(MessageWatcher):
    """
    Continuous watcher that:
    1. Opens each whitelisted group chat
    2. Reads visible messages
    3. Yields ChatMessage objects

    Intended for use in a polling loop.
    """

    def __init__(
        self,
        groups: list[str] | None = None,   # empty → monitor all
        poll_interval: float = 5.0,
        max_messages: int = 30,
    ):
        self.groups = set(groups) if groups else set()
        self.poll_interval = poll_interval
        self.max_messages = max_messages
        self._probe = WeChatWindowProbe()
        self._reader = WeChatMessageReader(max_messages=max_messages)
        self._seen: set[str] = set()   # hash of (group, sender, text) to avoid dupes within one session

    def _click_conversation(self, name: str) -> bool:
        """Click a conversation by name in the chat list."""
        if not _HAS_AUTO:
            return False
        try:
            win = _get_wechat_window()
            chat_list = _get_chat_list_control(win)
            if chat_list is None:
                return False
            for ctrl in chat_list.GetChildren():
                ctrl_name: str = getattr(ctrl, 'Name', '') or ''
                if ctrl_name == name:
                    ctrl.Click()
                    time.sleep(0.8)   # wait for chat to load
                    return True
        except Exception:
            pass
        return False

    def poll(self) -> Iterable[ChatMessage]:
        """
        Poll once: enumerate all groups, click each, read messages.
        Returns only new (unseen within this session) messages.
        """
        if not _HAS_AUTO:
            return []

        # Determine which groups to scan
        if self.groups:
            group_names = list(self.groups)
        else:
            all_convs = self._probe.list_conversation_names(limit=200)
            group_names = [n for n in all_convs if n]  # all are candidates

        results: list[ChatMessage] = []
        for group_name in group_names:
            if self.groups and group_name not in self.groups:
                continue
            if not self._click_conversation(group_name):
                continue
            for msg in self._reader.read_messages(group_name):
                # Deduplicate within this session
                h = hashlib.md5(f'{msg.group_name}|{msg.sender}|{msg.text}'.encode()).hexdigest()[:16]
                if h in self._seen:
                    continue
                self._seen.add(h)
                results.append(msg)
        return results


# ── Standalone probe script ─────────────────────────────────────────
def _main():
    probe = WeChatWindowProbe()
    if not probe.is_available():
        print('ERROR: WeChat is not running or UI Automation is not available.')
        return
    names = probe.list_conversation_names()
    print(f'Found {len(names)} conversation(s):')
    for n in names:
        print(f'  {n}')


if __name__ == '__main__':
    _main()
