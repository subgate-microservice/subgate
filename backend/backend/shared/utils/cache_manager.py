from abc import ABC, abstractmethod
from typing import Callable


class CacheManager(ABC):
    @abstractmethod
    def cache(self, fn: Callable, time: float) -> None:
        pass
