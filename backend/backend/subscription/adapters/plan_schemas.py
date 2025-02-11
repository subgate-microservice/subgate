from typing import Optional, Any
from uuid import uuid4

from pydantic import Field

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.subscription.domain.cycle import CycleCode, Cycle
from backend.subscription.domain.plan import UsageRate, Discount, Plan, PlanId


class PlanCreate(MyBase):
    id: PlanId = Field(default_factory=uuid4)
    title: str
    price: float
    currency: str
    billing_cycle: CycleCode
    description: Optional[str] = None
    level: int = 10
    features: Optional[str] = None
    usage_rates: list[UsageRate] = Field(default_factory=list)
    fields: dict[str, Any] = Field(default_factory=dict)
    discounts: list[Discount] = Field(default_factory=list)

    def to_plan(self, auth_id: AuthId):
        data = self.model_dump()
        data["billing_cycle"] = Cycle.from_code(self.billing_cycle)
        return Plan(auth_id=auth_id, **data)
