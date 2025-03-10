from abc import ABC, abstractmethod
from typing import Optional, Iterable

from pydantic import BaseModel, Field

from backend.shared.enums import Lock
from backend.webhook.domain.webhook import WebhookId, Webhook


class WebhookSby(BaseModel):
    ids: Optional[set[WebhookId]] = None
    auth_ids: Optional[set[WebhookId]] = None
    event_codes: Optional[set[str]] = None
    skip: int = 0
    limit: int = 100
    order_by: list[tuple[str, int]] = Field(default_factory=lambda: [("created_at", 1)])


class WebhookRepo(ABC):
    @abstractmethod
    async def add_one(self, item: Webhook) -> None:
        pass

    @abstractmethod
    async def add_many(self, items: Iterable[Webhook]) -> None:
        pass

    @abstractmethod
    async def update_one(self, item: Webhook) -> None:
        pass

    @abstractmethod
    async def get_one_by_id(self, item_id: WebhookId, lock: Lock = "write") -> Webhook:
        pass

    @abstractmethod
    async def get_selected(self, sby: WebhookSby, lock: Lock = "write") -> list[Webhook]:
        pass

    @abstractmethod
    async def delete_one(self, item: Webhook) -> None:
        pass

    @abstractmethod
    async def delete_many(self, items: Iterable[Webhook]) -> None:
        pass
