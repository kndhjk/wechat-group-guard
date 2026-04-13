from watcher.mock_file import MockFileWatcher
from detector.scoring import score_text
from review.queue import ReviewItem
from review.console import ask_for_review
from review.service import ReviewService
from storage.jsonl_store import append_jsonl
from storage.pending_store import PendingStore
from storage.decision_store import DecisionStore
from watcher.filtering import is_group_allowed

KEYWORDS = ['加V', '兼职', '刷单', '代写', '贷款', '返利', '推广']


def main():
    allowed_groups = ['示例微信群']
    watcher = MockFileWatcher('samples/mock_messages.json')

    review_service = ReviewService(PendingStore())
    decision_store = DecisionStore()

    for msg in watcher.poll():
        if not is_group_allowed(msg.group_name, allowed_groups):
            continue
        result = score_text(msg.text, KEYWORDS)
        append_jsonl('data/messages.jsonl', {
            'group_name': msg.group_name,
            'sender': msg.sender,
            'text': msg.text,
            'reasons': result.reasons,
            'score': result.score,
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
        decision = {
            'group_name': item.group_name,
            'sender': item.sender,
            'message': item.message,
            'reasons': item.reasons,
            'approved': approved,
        }
        append_jsonl('logs/review_actions.jsonl', decision)
        decision_store.append(decision)
        if approved:
            print(f'[TODO] Kick {item.sender} from {item.group_name}')


if __name__ == '__main__':
    main()
