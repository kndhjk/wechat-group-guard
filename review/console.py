from __future__ import annotations

from enum import Enum
from .queue import ReviewItem


class ReviewAction(Enum):
    KICK = 'kick'
    SKIP = 'skip'
    IGNORE_USER = 'ignore'
    MUTE = 'mute'        # future


def ask_for_review(item: ReviewItem) -> ReviewAction:
    print('\n=== Pending Review ===')
    print('Group :', item.group_name)
    print('Sender:', item.sender)
    print('Text  :', item.message[:120])
    if item.reasons:
        print('Reasons:', ', '.join(item.reasons))
    if item.score:
        print('Score :', item.score, '/ 100')

    print('Action? [k=kick / i=ignore user / s=skip] ', end='')
    answer = input().strip().lower()

    if answer == 'k':
        return ReviewAction.KICK
    elif answer == 'i':
        return ReviewAction.IGNORE_USER
    else:
        return ReviewAction.SKIP


def action_to_bool(action: ReviewAction) -> bool:
    """For backwards-compatible boolean decision."""
    return action == ReviewAction.KICK
