from dataclasses import asdict
from review.queue import ReviewItem
from storage.pending_store import PendingStore


class ReviewService:
    def __init__(self, store: PendingStore):
        self.store = store

    def enqueue(self, item: ReviewItem) -> None:
        self.store.add(asdict(item))
