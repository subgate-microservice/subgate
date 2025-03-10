from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Self, Literal, Iterable
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.enums import Lock
from backend.shared.event_driven.base_event import Event
from backend.shared.utils.dt import get_current_datetime


class SentErrorInfo(MyBase):
    status_code: int
    detail: str


class Message(MyBase):
    type: str
    event_code: str
    occurred_at: AwareDatetime
    payload: dict

    @classmethod
    def from_event(cls, event: Event):
        payload = event.model_dump(mode="json", exclude={"auth_id", "occurred_at"})
        payload.get("changes", {}).pop("updated_at", None)
        return cls(
            type="event",
            event_code=event.get_event_code(),
            occurred_at=event.occurred_at,
            payload=payload,
        )


class DeliveryTask(MyBase):
    id: UUID = Field(default_factory=uuid4)
    url: str
    data: Message
    delays: tuple[int, ...]
    partkey: str
    auth_id: AuthId
    status: Literal["unprocessed", "success_sent", "failed_sent",] = "unprocessed"
    retries: int = 0
    error_info: Optional[SentErrorInfo] = None
    last_retry_at: Optional[AwareDatetime] = None
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)

    @property
    def next_retry_at(self) -> Optional[AwareDatetime]:
        if self.status == "success_sent":
            return None
        if len(self.delays) <= self.retries:
            return None
        if self.status == "unprocessed":
            return get_current_datetime() + timedelta(seconds=self.delays[0])

        return self.last_retry_at + timedelta(seconds=self.delays[self.retries])

    @property
    def max_retries(self):
        return len(self.delays)

    def failed_sent(self, error_info: SentErrorInfo) -> Self:
        return self.model_copy(update={
            "status": "failed_sent",
            "retries": self.retries + 1,
            "error_info": error_info,
            "last_retry_at": get_current_datetime(),
        })

    def success_sent(self) -> Self:
        return self.model_copy(update={
            "status": "success_sent",
            "retries": self.retries + 1,
            "error_info": None,
            "last_retry_at": get_current_datetime(),
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
    async def delete_many_before_date(self, core_date: AwareDatetime) -> None:
        pass

    @abstractmethod
    async def get_all(self, lock: Lock = "write") -> list[DeliveryTask]:
        pass

    @abstractmethod
    async def get_deliveries_for_send(self, limit=500, lock: Lock = "write") -> list[DeliveryTask]:
        pass
