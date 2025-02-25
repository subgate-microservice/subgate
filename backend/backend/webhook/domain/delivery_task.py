from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Self, Literal, Iterable, Union
from uuid import uuid4

from pydantic import Field, AwareDatetime, model_validator

from backend.shared.base_models import MyBase
from backend.shared.enums import Lock
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime


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
        return cls(
            type="event",
            event_code=event.get_event_code(),
            occurred_at=event.occurred_at,
            payload=event.model_dump(mode="json", exclude={"auth_id", "occurred_at"})
        )


class DeliveryTask(MyBase):
    id: int = -1
    url: str
    data: Message
    partkey: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["unprocessed", "success_sent", "failed_sent",] = "unprocessed"
    retries: int = 0
    max_retries: int = 13
    delays: Union[int, tuple[int, ...]] = 1
    error_info: Optional[SentErrorInfo] = None
    last_retry_at: Optional[AwareDatetime] = None
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)

    @property
    def next_retry_at(self) -> Optional[AwareDatetime]:
        if self.retries >= self.max_retries - 1:
            return None
        if self.status == "success_sent":
            return None
        if self.status == "unprocessed":
            return get_current_datetime()

        delay = self.delays if isinstance(self.delays, int) else self.delays[self.retries]
        return self.last_retry_at + timedelta(seconds=delay)

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

    @model_validator(mode='after')
    def check_delays_len(self) -> Self:
        if isinstance(self.delays, tuple):
            if len(self.delays) != self.max_retries - 1:
                raise ValueError(f"Length of delays must be {self.max_retries - 1}. Real value is {len(self.delays)}")
        return self


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
