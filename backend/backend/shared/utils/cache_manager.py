import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, TypeVar, Generic

T = TypeVar("T")


class CacheManager(ABC):
    @abstractmethod
    def cache(self, fn: Callable, expiration_time: Optional[float] = None) -> Callable:
        pass

    @abstractmethod
    def set(self, key: str, value: T, expiration_time: Optional[float] = None) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        pass

    @abstractmethod
    def pop(self, key: str) -> Optional[T]:
        pass


class InMemoryCacheManager(CacheManager, Generic[T]):
    def __init__(self, expiration_time: Optional[float] = None):
        self._cache: dict[str, T] = {}
        self._expiry: dict[str, Optional[float]] = {}
        self._default_expiration_time = expiration_time

    def cache(self, fn: Callable, expiration_time: Optional[float] = None) -> Callable:
        raise NotImplementedError("The cache decorator is not implemented yet")

    def set(self, key: str, value: T, expiration_time: Optional[float] = None) -> None:
        expiry_time = expiration_time if expiration_time is not None else self._default_expiration_time
        self._cache[key] = value
        self._expiry[key] = time.time() + expiry_time if expiry_time is not None else None

    def get(self, key: str) -> Optional[T]:
        expiry = self._expiry.get(key)
        if expiry is None or time.time() < expiry:
            return self._cache.get(key)
        self.pop(key)
        return None

    def pop(self, key: str) -> Optional[T]:
        self._expiry.pop(key, None)
        return self._cache.pop(key, None)
