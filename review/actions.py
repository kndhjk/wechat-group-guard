from enum import Enum


class ReviewAction(str, Enum):
    APPROVE_KICK = 'approve_kick'
    SKIP = 'skip'
    IGNORE_USER = 'ignore_user'
