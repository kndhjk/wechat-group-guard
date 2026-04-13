from abc import ABC, abstractmethod
from typing import Iterable
from .models import ChatMessage


class MessageWatcher(ABC):
    @abstractmethod
    def poll(self) -> Iterable[ChatMessage]:
        raise NotImplementedError
