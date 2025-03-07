import functools
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, Any


class CacheManager(ABC):
    @abstractmethod
    def cache(self, fn: Callable, expiration_time: float) -> Callable:
        pass

    @abstractmethod
    def set[T](self, key: str, value: T, expiration_time: float) -> None:
        pass

    @abstractmethod
    def get[T](self, key: str) -> T:
        pass

    @abstractmethod
    def pop[T](self, key: str) -> Optional[T]:
        pass


class InMemoryCacheManager(CacheManager):
    def __init__(self, _expiration_time: float):
        self._cache: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}

    def cache(self, fn: Callable, expiration_time: float) -> Callable:

        @functools.wraps(fn)
        async def wrapped(*args, **kwargs):
            key = f"{fn.__name__}:{args}:{kwargs}"
            if key in self._cache and time.time() < self._expiry.get(key, 0):
                return self._cache[key]
            result = await fn(*args, **kwargs)
            self.set(key, result, expiration_time)
            return result

        return wrapped

    def set[T](self, key: str, value: T, expiration_time: float) -> None:
        self._cache[key] = value
        self._expiry[key] = time.time() + expiration_time

    def get[T](self, key: str) -> Optional[T]:
        if key in self._cache and time.time() < self._expiry.get(key, 0):
            return self._cache[key]
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return None

    def pop[T](self, key: str) -> Optional[T]:
        value = self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return value
