from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Self, Literal, Iterable
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.shared.base_models import MyBase
from backend.shared.enums import Lock
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime


class SentErrorInfo(MyBase):
    status_code: int
    detail: str


class Payload(MyBase):
    type: str = "event"
    event_code: str
    occurred_at: AwareDatetime
    payload: dict

    @classmethod
    def from_event(cls, event: Event):
        return cls(
            type="event",
            event_code=event.get_event_code(),
            occurred_at=event.occurred_at,
            payload=event.model_dump(mode="json", exclude={"auth_id", "occurred_at"})
        )


class DeliveryTask(MyBase):
    id: int = -1
    url: str
    data: Payload
    partkey: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["unprocessed", "success_sent", "failed_sent",] = "unprocessed"
    retries: int = 0
    max_retries: int = 13
    error_info: Optional[SentErrorInfo] = None
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)
    sent_at: AwareDatetime = Field(default_factory=get_current_datetime)
    next_retry_at: Optional[AwareDatetime] = Field(default_factory=get_current_datetime)

    def _get_next_retry(self) -> Optional[AwareDatetime]:
        if self.retries + 1 >= self.max_retries:
            return None
        return get_current_datetime() + timedelta(seconds=1)

    def failed_sent(self, error_info: SentErrorInfo) -> Self:
        next_retry_at = self._get_next_retry()

        return self.model_copy(update={
            "status": "failed_sent",
            "retries": self.retries + 1,
            "next_retry_at": next_retry_at,
            "error_info": error_info,
            "sent_at": get_current_datetime(),
            "updated_at": get_current_datetime(),
        })

    def success_sent(self) -> Self:
        return self.model_copy(update={
            "status": "success_sent",
            "retries": self.retries + 1,
            "next_retry_at": None,
            "error_info": None,
            "sent_at": get_current_datetime(),
            "updated_at": get_current_datetime(),
        })


class DeliveryTaskRepo(ABC):
    @abstractmethod
    async def add_one(self, item: DeliveryTask) -> None:
        pass

    @abstractmethod
    async def add_many(self, items: Iterable[DeliveryTask]) -> None:
        pass

    @abstractmethod
    async def update_one(self, item: DeliveryTask) -> None:
        pass

    @abstractmethod
    async def update_many(self, items: Iterable[DeliveryTask]) -> None:
        pass

    @abstractmethod
    async def delete_one(self, item: DeliveryTask) -> None:
        pass

    @abstractmethod
    async def get_all(self, lock: Lock = "write") -> list[DeliveryTask]:
        pass

    @abstractmethod
    async def get_deliveries_for_send(self, limit=500, lock: Lock = "write") -> list[DeliveryTask]:
        pass
