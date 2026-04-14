"""
Desktop WeChat kick executor.

Implements the actual removal of a member from a WeChat group after
human review has approved the action.

Requires WeChat desktop for Windows to be running.

How it works:
1. Click the group conversation (opens it)
2. Click the group member count/member button → opens member list
3. Search for the target sender's name in the member list
4. Right-click → Remove from group
5. Confirm the removal (WeChat may show a confirmation button)
6. Log the outcome

All steps are wrapped in try/except so a single failure does not crash the loop.
"""

from __future__ import annotations

import time
import logging
from typing import Optional

# ── uiautomation import (Windows only) ──────────────────────────────
try:
    import uiautomation as auto
    _HAS_AUTO = True
except ImportError:
    auto = None
# ───────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

_WECHAT_WINDOW = '微信'
_MEMBER_AREA_NAME = '成员'
_CHAT_AREA_NAME = ''


def _get_wechat_window() -> auto.WindowControl:
    if auto is None:
        raise RuntimeError('uiautomation not installed')
    win = auto.WindowControl(searchDepth=1, Name=_WECHAT_WINDOW)
    if not win.Exists(3):
        raise RuntimeError('WeChat window not found')
    return win


def _click_conversation(win: auto.WindowControl, name: str) -> bool:
    """Click a conversation entry in the left chat list by name."""
    # The chat list is usually the first List control
    list_ctrl = None
    for ctrl in win.GetChildren():
        ct = str(getattr(ctrl, 'ControlType', '')) or ''
        if 'List' in ct:
            list_ctrl = ctrl
            break
    if list_ctrl is None:
        return False
    try:
        for item in list_ctrl.GetChildren():
            item_name: str = getattr(item, 'Name', '') or ''
            if item_name == name:
                item.Click()
                time.sleep(1.0)   # wait for chat to fully open
                return True
    except Exception as e:
        logger.warning('Failed to click conversation %r: %s', name, e)
    return False


def _open_member_list(win: auto.WindowControl) -> Optional[auto.Control]:
    """
    Click the group member area button inside the open chat.
    In WeChat desktop, the member count button is usually a Text control
    near the top-right of the chat pane (showing e.g. "5人").
    """
    try:
        # Walk all controls in the chat window
        for ctrl in win.GetChildren():
            name: str = getattr(ctrl, 'Name', '') or ''
            ct: str = str(getattr(ctrl, 'ControlType', '')) or ''
            # The member button typically contains "人" and is a button or text control
            if ('人' in name or _MEMBER_AREA_NAME in name) and ('Button' in ct or 'Text' in ct):
                ctrl.Click()
                time.sleep(0.8)
                # After clicking, the member list pane should appear
                for child in win.GetChildren():
                    child_name: str = getattr(child, 'Name', '') or ''
                    if '成员' in child_name or 'member' in child_name.lower():
                        return child
                return ctrl   # return what we clicked even if list didn't appear
    except Exception as e:
        logger.warning('Failed to open member list: %s', e)
    return None


def _find_member_in_list(
    member_list: auto.Control,
    sender: str,
) -> Optional[auto.Control]:
    """
    Search the member list for an entry matching `sender`.
    WeChat group member list entries are typically ListItem controls
    showing the member's WeChat nickname.
    """
    if member_list is None:
        return None
    sender_lower = sender.lower()
    try:
        for item in member_list.GetChildren():
            item_name: str = getattr(item, 'Name', '') or ''
            if sender_lower in item_name.lower() or item_name == sender:
                return item
            # Also check nested children (list may be hierarchical)
            for child in item.GetChildren():
                child_name: str = getattr(child, 'Name', '') or ''
                if sender_lower in child_name.lower() or child_name == sender:
                    return child
    except Exception as e:
        logger.warning('Failed to find member %r in list: %s', sender, e)
    return None


def _confirm_removal(win: auto.WindowControl) -> bool:
    """
    Look for a confirmation dialog / button after right-click removal.
    Common button text: "确定", "Remove", "移除", "Yes"
    """
    time.sleep(0.5)
    for ctrl in win.GetChildren():
        name: str = getattr(ctrl, 'Name', '') or ''
        ct: str = str(getattr(ctrl, 'ControlType', '')) or ''
        if 'Button' in ct:
            n = name.strip()
            if n in ('确定', '移除', 'Remove', '删除', 'Yes', '确认'):
                ctrl.Click()
                time.sleep(0.5)
                return True
    # Also try to find any popup window
    for child in auto.WindowControl(searchDepth=2).GetChildren():
        name = getattr(child, 'Name', '') or ''
        if '确定' in name or 'Remove' in name:
            child.Click()
            time.sleep(0.5)
            return True
    return False


class DesktopWeChatKickExecutor:
    """
    Real WeChat group kick executor using UI Automation.

    Safety: this should ONLY be called after explicit human approval.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def kick(self, group_name: str, sender: str) -> dict:
        """
        Remove `sender` from `group_name`.

        Returns a dict with keys:
          success (bool)
          message (str)
          steps (list[str])

        If dry_run=True, simulates the steps without actually clicking.
        """
        if auto is None:
            return {'success': False, 'message': 'uiautomation not installed', 'steps': []}

        steps: list[str] = []
        result: dict = {'success': False, 'message': '', 'steps': steps}

        try:
            if self.dry_run:
                steps.append(f'[DRY RUN] Would click conversation: {group_name}')
                steps.append(f'[DRY RUN] Would open member list')
                steps.append(f'[DRY RUN] Would locate member: {sender}')
                steps.append(f'[DRY RUN] Would right-click → remove → confirm')
                result['success'] = True
                result['message'] = 'dry_run=true — no actual action taken'
                logger.info('kick dry_run for %s from %s', sender, group_name)
                return result

            # ── Real execution ──────────────────────────────────────
            steps.append(f'click conversation: {group_name}')
            win = _get_wechat_window()
            if not _click_conversation(win, group_name):
                result['message'] = f'Could not open group chat: {group_name}'
                return result

            steps.append('open member list')
            member_list = _open_member_list(win)
            if member_list is None:
                result['message'] = 'Could not open member list'
                return result

            steps.append(f'find member: {sender}')
            member_item = _find_member_in_list(member_list, sender)
            if member_item is None:
                result['message'] = f'Member "{sender}" not found in group'
                return result

            steps.append('right-click → remove')
            member_item.RightClick()
            time.sleep(0.5)

            # Try to find and click "Remove" in the context menu
            found_remove = False
            for popup in auto.WindowControl(searchDepth=2).GetChildren():
                for ctrl in popup.GetChildren():
                    name: str = getattr(ctrl, 'Name', '') or ''
                    if '移除' in name or '删除' in name or 'Remove' in name:
                        ctrl.Click()
                        found_remove = True
                        break
                if found_remove:
                    break

            if not found_remove:
                result['message'] = 'Context menu did not show remove option'
                return result

            steps.append('confirm removal')
            if not _confirm_removal(win):
                logger.warning('Confirmation step could not find confirm button')

            result['success'] = True
            result['message'] = f'Successfully removed {sender} from {group_name}'
            steps.append('done')
            logger.info('Kicked %s from %s', sender, group_name)

        except Exception as e:
            result['message'] = f'Error during kick: {e}'
            steps.append(f'ERROR: {e}')
            logger.exception('kick failed for %s from %s', sender, group_name)

        return result
