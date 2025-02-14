from typing import Optional, Any, Self
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.subscription import SubId, Subscription, SubscriptionStatus, PlanInfo, BillingInfo
from backend.subscription.domain.usage import UsageRate, Usage


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


class UsageSchema(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    used_units: float
    last_renew: AwareDatetime

    @classmethod
    def from_usage(cls, usage: Usage) -> Self:
        return cls(title=usage.title, code=usage.code, unit=usage.unit, available_units=usage.available_units,
                   renew_cycle=usage.renew_cycle, used_units=usage.used_units, last_renew=usage.last_renew)

    def to_usage(self) -> Usage:
        return Usage(title=self.title, code=self.code, unit=self.unit, available_units=self.available_units,
                     renew_cycle=self.renew_cycle, used_units=self.used_units, last_renew=self.last_renew)


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
        return Plan(title=self.title, price=self.price, currency=self.currency, auth_id=auth_id,
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
        return PlanUpdate(
            id=plan.id, title=plan.title, price=plan.price, currency=plan.currency, billing_cycle=plan.billing_cycle,
            description=plan.description, level=plan.level, features=plan.features,
            usage_rates=plan.usage_rates.get_all(), fields=plan.fields, discounts=plan.discounts.get_all(),
        )

    def to_plan(self, auth_id: AuthId, created_at: AwareDatetime):
        usage_rates = [x.to_usage_rate() for x in self.usage_rates]
        discounts = [x.to_discount() for x in self.discounts]
        return Plan.create_unsafe(
            id=self.id, title=self.title, price=self.price, currency=self.currency, billing_cycle=self.billing_cycle,
            description=self.description, level=self.level, features=self.features, usage_rates=usage_rates,
            discounts=discounts, fields=self.fields, auth_id=auth_id, created_at=created_at,
            updated_at=get_current_datetime(),
        )


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


class PlanInfoSchema(MyBase):
    plan_id: PlanId
    title: str
    description: Optional[str]
    level: int
    features: Optional[str]

    @classmethod
    def from_plan_info(cls, plan_info: PlanInfo) -> Self:
        return cls(plan_id=plan_info.id, title=plan_info.title, description=plan_info.description,
                   level=plan_info.level, features=plan_info.features)

    def to_plan_info(self):
        return PlanInfo(id=self.plan_id, title=self.title, description=self.description, level=self.level,
                        features=self.features)


class BillingInfoSchema(MyBase):
    price: float
    currency: str
    billing_cycle: Period
    last_billing: AwareDatetime

    @classmethod
    def from_billing_info(cls, billing_info: BillingInfo) -> Self:
        return cls(price=billing_info.price, currency=billing_info.currency,
                   billing_cycle=billing_info.billing_cycle, last_billing=billing_info.last_billing)

    def to_billing_info(self) -> BillingInfo:
        return BillingInfo(price=self.price, currency=self.currency, billing_cycle=self.billing_cycle,
                           last_billing=self.last_billing)


class SubscriptionCreate(MyBase):
    id: SubId = Field(default_factory=uuid4)
    subscriber_id: str
    plan_info: PlanInfoSchema
    billing_info: BillingInfoSchema
    status: SubscriptionStatus = SubscriptionStatus.Active
    paused_from: Optional[AwareDatetime] = None
    autorenew: bool = False
    usages: list[UsageSchema] = Field(default_factory=list)
    discounts: list[DiscountSchema] = Field(default_factory=list)
    fields: dict = Field(default_factory=dict)

    @classmethod
    def from_subscription(cls, sub: Subscription) -> Self:
        plan_info = PlanInfoSchema.from_plan_info(sub.plan_info)
        billing_info = BillingInfoSchema.from_billing_info(sub.billing_info)
        usages = [UsageSchema.from_usage(x) for x in sub.usages]
        discounts = [DiscountSchema.from_discount(x) for x in sub.discounts]
        return cls(
            id=sub.id,
            subscriber_id=sub.subscriber_id,
            plan_info=plan_info,
            billing_info=billing_info,
            status=sub.status,
            paused_from=sub.paused_from,
            autorenew=sub.autorenew,
            usages=usages,
            discounts=discounts,
            fields=sub.fields,
        )

    def to_subscription(self, auth_id: AuthId) -> Subscription:
        dt = get_current_datetime()
        usages = [x.to_usage() for x in self.usages]
        discounts = [x.to_discount() for x in self.discounts]
        plan_info = self.plan_info.to_plan_info()
        billing_info = self.billing_info.to_billing_info()
        return Subscription.create_unsafe(
            id=self.id,
            subscriber_id=self.subscriber_id,
            plan_info=plan_info,
            billing_info=billing_info,
            status=self.status,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=usages,
            discounts=discounts,
            fields=self.fields,
            auth_id=auth_id,
            created_at=dt,
            updated_at=dt,
        )


class SubscriptionUpdate(MyBase):
    id: SubId
    subscriber_id: str
    plan_info: PlanInfo
    billing_info: BillingInfo
    status: SubscriptionStatus
    paused_from: Optional[AwareDatetime]
    autorenew: bool
    usages: list[UsageSchema]
    discounts: list[DiscountSchema]
    fields: dict

    @classmethod
    def from_subscription(cls, sub: Subscription) -> Self:
        plan_info = PlanInfoSchema.from_plan_info(sub.plan_info)
        billing_info = BillingInfoSchema.from_billing_info(sub.billing_info)
        usages = [UsageSchema.from_usage(x) for x in sub.usages]
        discounts = [DiscountSchema.from_discount(x) for x in sub.discounts]
        return cls(
            id=sub.id,
            subscriber_id=sub.subscriber_id,
            plan_info=plan_info,
            billing_info=billing_info,
            status=sub.status,
            paused_from=sub.paused_from,
            autorenew=sub.autorenew,
            usages=usages,
            discounts=discounts,
            fields=sub.fields,
        )

    def to_subscription(self, auth_id: AuthId, created_at: AwareDatetime) -> Subscription:
        usages = [x.to_usage() for x in self.usages]
        discounts = [x.to_discount() for x in self.discounts]
        updated_at = get_current_datetime()
        return Subscription.create_unsafe(
            id=self.id,
            subscriber_id=self.subscriber_id,
            plan_info=self.plan_info,
            billing_info=self.billing_info,
            status=self.status,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=usages,
            discounts=discounts,
            fields=self.fields,
            auth_id=auth_id,
            created_at=created_at,
            updated_at=updated_at,
        )


class SubscriptionRetrieve(MyBase):
    id: SubId
    subscriber_id: str
    plan_info: PlanInfo
    billing_info: BillingInfo
    status: SubscriptionStatus
    paused_from: Optional[AwareDatetime]
    autorenew: bool
    usages: list[UsageSchema]
    discounts: list[DiscountSchema]
    fields: dict
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @classmethod
    def from_subscription(cls, sub: Subscription) -> Self:
        plan_info = PlanInfoSchema.from_plan_info(sub.plan_info)
        billing_info = BillingInfoSchema.from_billing_info(sub.billing_info)
        usages = [UsageSchema.from_usage(x) for x in sub.usages]
        discounts = [DiscountSchema.from_discount(x) for x in sub.discounts]
        return cls(
            id=sub.id,
            subscriber_id=sub.subscriber_id,
            plan_info=plan_info,
            billing_info=billing_info,
            status=sub.status,
            paused_from=sub.paused_from,
            autorenew=sub.autorenew,
            usages=usages,
            discounts=discounts,
            fields=sub.fields,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )
