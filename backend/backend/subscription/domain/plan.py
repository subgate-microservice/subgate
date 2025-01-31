from datetime import timedelta
from typing import Any, Optional, Self
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime, model_validator

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.exceptions import ItemAlreadyExist
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Cycle

PlanId = UUID


class UsageRate(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Cycle


class Usage(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Cycle
    last_renew: AwareDatetime = Field(default_factory=get_current_datetime)
    used_units: float

    def renew(self) -> Self:
        return self.model_copy(update={
            "used_units": 0,
            "last_renew": get_current_datetime(),
        })

    @property
    def need_to_renew(self) -> bool:
        return get_current_datetime() > self.renew_cycle.get_next_billing_date(self.last_renew)

    @property
    def next_renew(self) -> AwareDatetime:
        return self.last_renew + timedelta(self.renew_cycle.cycle_in_days)


class Discount(MyBase):
    title: str
    code: str
    description: str
    size: float = Field(ge=0, le=1)
    valid_until: Optional[AwareDatetime]


class Plan(MyBase):
    id: PlanId = Field(default_factory=uuid4)
    title: str
    price: float
    currency: str
    billing_cycle: Cycle
    description: str = ""
    level: int = 1
    features: Optional[str] = None
    usage_rates: list[UsageRate] = Field(default_factory=list, )
    fields: dict[str, Any] = Field(default_factory=dict)
    auth_id: AuthId = Field(exclude=True)
    discounts: list[Discount] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)

    @model_validator(mode="after")
    def _validate_other(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at earlier than created_at")
        return self

    @model_validator(mode="after")
    def _validate_usage_rates(self) -> Self:
        hashes = set()
        for rate in self.usage_rates:
            if rate.code in hashes:
                raise ItemAlreadyExist(item_type=UsageRate, index_key="code", index_value=rate.code)
            hashes.add(rate.code)
        return self

    @model_validator(mode="after")
    def _validate_discounts(self) -> Self:
        hashes = set()
        for discount in self.discounts:
            if discount.code in hashes:
                raise ItemAlreadyExist(item_type=Discount, index_key="code", index_value=discount.code)
            hashes.add(discount.code)
        return self
