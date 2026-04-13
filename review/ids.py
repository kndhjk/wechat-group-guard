import hashlib


def make_review_id(group_name: str, sender: str, message: str) -> str:
    raw = f'{group_name}|{sender}|{message}'.encode('utf-8')
    return hashlib.sha1(raw).hexdigest()[:12]
