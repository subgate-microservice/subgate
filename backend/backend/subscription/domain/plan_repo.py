from abc import ABC, abstractmethod
from typing import Optional, Iterable

from pydantic import BaseModel, Field, ConfigDict

from backend.auth.domain.auth_user import AuthId
from backend.shared.enums import Lock
from backend.subscription.domain.plan import PlanId, Plan


class PlanSby(BaseModel):
    ids: Optional[set[PlanId]] = None
    auth_ids: Optional[set[AuthId]] = None
    skip: int = 0
    limit: int = 100
    order_by: list[tuple[str, int]] = Field(default_factory=lambda: [("created_at", 1)])

    model_config = ConfigDict(extra="forbid")


class PlanRepo(ABC):
    @abstractmethod
    async def create_indexes(self):
        pass

    @abstractmethod
    async def add_one(self, item: Plan) -> None:
        pass

    @abstractmethod
    async def add_many(self, items: Iterable[Plan]) -> None:
        pass

    @abstractmethod
    async def update_one(self, item: Plan) -> None:
        pass

    @abstractmethod
    async def get_one_by_id(self, item_id: PlanId, lock: Lock = "write") -> Plan:
        pass

    @abstractmethod
    async def get_selected(self, sby: PlanSby, lock: Lock = "write") -> list[Plan]:
        pass

    @abstractmethod
    async def delete_one(self, item: Plan) -> None:
        pass

    @abstractmethod
    async def delete_many(self, items: Iterable[Plan]) -> None:
        pass
