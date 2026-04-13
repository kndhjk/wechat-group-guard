from watcher.mock_file import MockFileWatcher
from detector.scoring import score_text
from review.queue import ReviewItem
from review.console import ask_for_review
from review.service import ReviewService
from review.ids import make_review_id
from storage.jsonl_store import append_jsonl
from storage.pending_store import PendingStore
from storage.decision_store import DecisionStore
from watcher.filtering import is_group_allowed
from watcher.dedup import DedupCache
from storage.ignore_store import IgnoreStore

KEYWORDS = ['加V', '兼职', '刷单', '代写', '贷款', '返利', '推广']


def main():
    allowed_groups = ['示例微信群']
    watcher = MockFileWatcher('samples/mock_messages.json')

    review_service = ReviewService(PendingStore())
    decision_store = DecisionStore()
    ignore_store = IgnoreStore()
    dedup = DedupCache()

    for msg in watcher.poll():
        if not is_group_allowed(msg.group_name, allowed_groups):
            continue
        if ignore_store.contains(msg.sender):
            continue
        if dedup.seen(msg.group_name, msg.sender, msg.text):
            continue
        result = score_text(msg.text, KEYWORDS)
        review_id = make_review_id(msg.group_name, msg.sender, msg.text)
        append_jsonl('data/messages.jsonl', {
            'review_id': review_id,
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
            'review_id': review_id,
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
