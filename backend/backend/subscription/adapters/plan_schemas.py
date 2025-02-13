from typing import Optional, Any
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import UsageRate, Discount, Plan, PlanId


class PlanCreate(MyBase):
    id: PlanId = Field(default_factory=uuid4)
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str] = None
    level: int = 10
    features: Optional[str] = None
    usage_rates: list[UsageRate] = Field(default_factory=list)
    fields: dict[str, Any] = Field(default_factory=dict)
    discounts: list[Discount] = Field(default_factory=list)

    def to_plan(self, auth_id: AuthId):
        data = self.model_dump()
        return Plan(auth_id=auth_id, **data)


class PlanUpdate(MyBase):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str]
    level: int
    features: Optional[str]
    usage_rates: list[UsageRate]
    fields: dict[str, Any]
    discounts: list[Discount]

    def to_plan(self, auth_id: AuthId, created_at: AwareDatetime):
        data = self.model_dump()
        return Plan(auth_id=auth_id, created_at=created_at, **data)
