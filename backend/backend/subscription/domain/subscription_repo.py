from abc import ABC, abstractmethod
from typing import Optional, Iterable

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import BaseSby
from backend.shared.enums import Lock
from backend.subscription.domain.subscription import SubId, Subscription, SubscriptionStatus


class SubscriptionSby(BaseSby):
    ids: Optional[set[SubId]] = None
    statuses: Optional[set[SubscriptionStatus]] = None
    auth_ids: Optional[set[AuthId]] = None
    subscriber_ids: Optional[set[str]] = None
    expiration_date_lt: Optional[AwareDatetime] = None
    usage_renew_date_lt: Optional[AwareDatetime] = None


class SubscriptionRepo(ABC):
    @abstractmethod
    async def create_indexes(self):
        pass

    @abstractmethod
    async def add_one(self, item: Subscription) -> None:
        pass

    @abstractmethod
    async def add_many(self, items: Iterable[Subscription]) -> None:
        pass

    @abstractmethod
    async def update_one(self, item: Subscription) -> None:
        pass

    @abstractmethod
    async def get_selected(self, sby: SubscriptionSby, lock: Lock = "write") -> list[Subscription]:
        pass

    @abstractmethod
    async def get_one_by_id(self, sub_id: SubId, lock: Lock = "write") -> Subscription:
        pass

    @abstractmethod
    async def get_subscriber_active_one(self, subscriber_id: str, auth_id: AuthId, lock: Lock = "write") -> Optional[Subscription]:
        pass

    @abstractmethod
    async def delete_many(self, items: Iterable[Subscription]) -> None:
        pass
