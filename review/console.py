from .queue import ReviewItem


def ask_for_review(item: ReviewItem) -> bool:
    print('\n=== Pending Review ===')
    print('Group :', item.group_name)
    print('Sender:', item.sender)
    print('Text  :', item.message)
    print('Reasons:', ', '.join(item.reasons))
    answer = input('Action? [k=kick / s=skip] ').strip().lower()
    return answer == 'k'
