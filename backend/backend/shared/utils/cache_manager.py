import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, Any


class CacheManager(ABC):
    @abstractmethod
    def cache(self, fn: Callable, expiration_time: float = None) -> Callable:
        pass

    @abstractmethod
    def set[T](self, key: str, value: T, expiration_time: float = None) -> None:
        pass

    @abstractmethod
    def get[T](self, key: str) -> T:
        pass

    @abstractmethod
    def pop[T](self, key: str) -> Optional[T]:
        pass


class InMemoryCacheManager(CacheManager):
    def __init__(self, expiration_time: float = None):
        self._cache: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._expiration_time = expiration_time

    def cache(self, fn: Callable, expiration_time: float = None) -> Callable:
        raise NotImplemented

    def set[T](self, key: str, value: T, expiration_time: float = None) -> None:
        expiration_time = expiration_time if expiration_time is not None else self._expiration_time
        self._cache[key] = value
        self._expiry[key] = time.time() + expiration_time if expiration_time is not None else None

    def get[T](self, key: str) -> Optional[T]:
        if key in self._cache:
            expiry = self._expiry[key]
            if expiry is not None and time.time() < expiry:
                return self._cache[key]
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return None

    def pop[T](self, key: str) -> Optional[T]:
        value = self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return value
