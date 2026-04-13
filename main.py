from watcher.mock import MockWatcher
from detector.rules import detect_text
from review.queue import ReviewItem
from review.console import ask_for_review
from review.service import ReviewService
from storage.jsonl_store import append_jsonl
from storage.pending_store import PendingStore
from watcher.filtering import is_group_allowed

KEYWORDS = ['加V', '兼职', '刷单', '代写', '贷款', '返利', '推广']


def main():
    allowed_groups = ['示例微信群']
    watcher = MockWatcher([
        {'group_name': '示例微信群', 'sender': '某广告号', 'text': '加V看兼职，日结，联系vx abc123'},
        {'group_name': '示例微信群', 'sender': '正常成员', 'text': '今晚吃什么'},
    ])

    review_service = ReviewService(PendingStore())

    for msg in watcher.poll():
        if not is_group_allowed(msg.group_name, allowed_groups):
            continue
        result = detect_text(msg.text, KEYWORDS)
        append_jsonl('data/messages.jsonl', {
            'group_name': msg.group_name,
            'sender': msg.sender,
            'text': msg.text,
            'reasons': result.reasons,
            'suspicious': result.suspicious,
            'timestamp': msg.timestamp.isoformat(),
        })
        if not result.suspicious:
            continue
        item = ReviewItem(
            group_name=msg.group_name,
            sender=msg.sender,
            message=msg.text,
            reasons=result.reasons,
        )
        review_service.enqueue(item)
        approved = ask_for_review(item)
        append_jsonl('logs/review_actions.jsonl', {
            'group_name': item.group_name,
            'sender': item.sender,
            'message': item.message,
            'reasons': item.reasons,
            'approved': approved,
        })
        if approved:
            print(f'[TODO] Kick {item.sender} from {item.group_name}')


if __name__ == '__main__':
    main()
