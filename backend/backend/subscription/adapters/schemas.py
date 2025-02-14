from typing import Optional, Any, Self
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.usage import UsageRate


class UsageRateSchema(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period

    @classmethod
    def from_usage_rate(cls, usage_rate: UsageRate) -> Self:
        return cls(code=usage_rate.code, title=usage_rate.title, unit=usage_rate.unit,
                   availbale_units=usage_rate.available_units, renew_cycle=usage_rate.renew_cycle)

    def to_usage_rate(self) -> UsageRate:
        return UsageRate(title=self.title, code=self.code, unit=self.unit, available_units=self.available_units,
                         renew_cycle=self.renew_cycle)


class DiscountSchema(MyBase):
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: Optional[AwareDatetime]

    @classmethod
    def from_discount(cls, discount: Discount) -> Self:
        return cls(title=discount.title, code=discount.code, description=discount.description, size=discount.size,
                   valid_until=discount.valid_until)

    def to_discount(self) -> Discount:
        return Discount(title=self.title, code=self.code, description=self.description, size=self.size,
                        valid_until=self.valid_until)


class PlanCreate(MyBase):
    id: PlanId = Field(default_factory=uuid4)
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str] = None
    level: int = 10
    features: Optional[str] = None
    usage_rates: list[UsageRateSchema] = Field(default_factory=list)
    fields: dict[str, Any] = Field(default_factory=dict)
    discounts: list[DiscountSchema] = Field(default_factory=list)

    @classmethod
    def from_plan(cls, plan: Plan) -> Self:
        return cls(id=plan.id, title=plan.title, price=plan.price, currency=plan.currency,
                   billing_cycle=plan.billing_cycle, description=plan.description, level=plan.level,
                   features=plan.features, usage_rates=plan.usage_rates.get_all(), fields=plan.fields,
                   discounts=plan.discounts.get_all())

    def to_plan(self, auth_id: AuthId):
        usage_rates = [x.to_usage_rate() for x in self.usage_rates]
        discounts = [x.to_discount() for x in self.discounts]
        return Plan.create(title=self.title, price=self.price, currency=self.currency, auth_id=auth_id,
                           billing_cycle=self.billing_cycle, description=self.description, level=self.level,
                           features=self.features, usage_rates=usage_rates, discounts=discounts, fields=self.fields,
                           id=self.id)


class PlanUpdate(MyBase):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str]
    level: int
    features: Optional[str]
    usage_rates: list[UsageRateSchema]
    fields: dict[str, Any]
    discounts: list[DiscountSchema]

    @classmethod
    def from_plan(cls, plan: Plan) -> Self:
        return PlanUpdate(id=plan.id, title=plan.title, price=plan.price, currency=plan.currency,
                          billing_cycle=plan.billing_cycle, description=plan.description, level=plan.level,
                          features=plan.features, usage_rates=plan.usage_rates.get_all(),
                          fields=plan.fields, discounts=plan.discounts.get_all(),
                          )

    def to_plan(self, auth_id: AuthId, created_at: AwareDatetime):
        usage_rates = [x.to_usage_rate() for x in self.usage_rates]
        discounts = [x.to_discount() for x in self.discounts]
        return Plan(id=self.id, title=self.title, price=self.price, currency=self.currency,
                    billing_cycle=self.billing_cycle, description=self.description, level=self.level,
                    features=self.features, usage_rates=usage_rates, discounts=discounts, fields=self.fields,
                    auth_id=auth_id, created_at=created_at, updated_at=get_current_datetime(), )


class PlanRetrieve(MyBase):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str]
    level: int
    features: Optional[str]
    usage_rates: list[UsageRateSchema]
    fields: dict[str, Any]
    discounts: list[DiscountSchema]
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @classmethod
    def from_plan(cls, plan: Plan):
        return PlanRetrieve(
            id=plan.id,
            title=plan.title,
            price=plan.price,
            currency=plan.currency,
            billing_cycle=plan.billing_cycle,
            description=plan.description,
            level=plan.level,
            features=plan.features,
            usage_rates=plan.usage_rates.get_all(),
            fields=plan.fields,
            discounts=plan.discounts.get_all(),
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
