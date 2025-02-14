import dataclasses
from datetime import timedelta
from typing import Any, Optional, Self
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.event_driven.base_event import Event
from backend.shared.item_maanger import ItemManager
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.usage import UsageRate

PlanId = UUID


class UsageOld(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
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
        return self.last_renew + timedelta(self.renew_cycle.get_cycle_in_days())


class UsageRateOld(MyBase):
    code: str
    title: str
    unit: str
    available_units: float
    renew_cycle: Period

    @classmethod
    def from_usage(cls, usage: UsageOld):
        return cls(code=usage.code, title=usage.title, unit=usage.unit, available_units=usage.available_units,
                   renew_cycle=usage.renew_cycle)


class DiscountOld(MyBase):
    title: str
    code: str
    description: Optional[str] = None
    size: float = Field(ge=0, le=1)
    valid_until: Optional[AwareDatetime]


@dataclasses.dataclass(frozen=True)
class PlanCreated(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    created_at: AwareDatetime


@dataclasses.dataclass(frozen=True)
class PlanDeleted(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    deleted_at: AwareDatetime


@dataclasses.dataclass(frozen=True)
class PlanUpdated(Event):
    id: PlanId
    updated_at: AwareDatetime
    updated_fields: list[str]


class Plan:
    def __init__(
            self,
            id: PlanId,
            title: str,
            price: float,
            currency: str,
            billing_cycle: Period,
            description: Optional[str],
            level: int,
            features: Optional[str],
            usage_rates: list[UsageRate],
            discounts: list[Discount],
            fields: dict[str, Any],
            auth_id: AuthId,
            created_at: AwareDatetime,
            updated_at: AwareDatetime,
    ):
        self.title = title
        self.price = price
        self.currency = currency
        self.billing_cycle = billing_cycle
        self.description = description
        self.level = level
        self.features = features
        self.fields = fields
        self.auth_id = auth_id

        self._id = id
        self._usage_rates = ItemManager(usage_rates, lambda x: x.code)
        self._discounts = ItemManager(discounts, lambda x: x.code)
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def id(self):
        return self._id

    @property
    def usage_rates(self) -> ItemManager[UsageRate]:
        return self._usage_rates

    @property
    def discounts(self) -> ItemManager[Discount]:
        return self._discounts

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at

    @classmethod
    def create(
            cls,
            title: str,
            price: float,
            currency: str,
            auth_id: AuthId,
            billing_cycle: Period = Period.Monthly,
            description: str = None,
            level: int = 10,
            features: str = None,
            usage_rates: list[UsageRate] = None,
            discounts: list[Discount] = None,
            fields: dict = None,
            id: PlanId = None,
    ) -> Self:
        dt = get_current_datetime()
        id = id if id else uuid4()
        fields = fields if fields is not None else {}
        usage_rates = usage_rates if usage_rates is not None else []
        discounts = discounts if discounts is not None else []
        instance = cls(id, title, price, currency, billing_cycle, description, level, features, usage_rates, discounts,
                       fields, auth_id, dt, dt)
        return instance


class PlanEventFactory:
    def __init__(self, plan: Plan):
        self.plan = plan

    def plan_created(self) -> PlanCreated:
        return PlanCreated(self.plan.id, self.plan.title, self.plan.price, self.plan.currency, self.plan.billing_cycle,
                           self.plan.auth_id, self.plan.created_at)

    def plan_deleted(self) -> PlanDeleted:
        dt = get_current_datetime()
        return PlanDeleted(self.plan.id, self.plan.title, self.plan.price, self.plan.currency, self.plan.billing_cycle,
                           self.plan.auth_id, dt)

    def plan_updated(self, new_plan: Plan) -> PlanUpdated:
        old_plan = self.plan
        updated_fields = []

        # Проверяем простые атрибуты
        for field in (
                "title", "price", "currency", "billing_cycle", "description", "level", "features", "fields", "auth_id"
        ):
            if getattr(old_plan, field) != getattr(new_plan, field):
                updated_fields.append(field)

        # Проверяем usage_rates
        old_usage = {u.code: u for u in old_plan.usage_rates}
        new_usage = {u.code: u for u in new_plan.usage_rates}

        added_usage = set(new_usage) - set(old_usage)
        removed_usage = set(old_usage) - set(new_usage)
        changed_usage = {code for code in old_usage if code in new_usage and old_usage[code] != new_usage[code]}

        if added_usage or removed_usage or changed_usage:
            updated_fields.append("usage_rates")

        # Проверяем discounts
        old_discounts = {d.code: d for d in old_plan.discounts}
        new_discounts = {d.code: d for d in new_plan.discounts}

        added_discounts = set(new_discounts) - set(old_discounts)
        removed_discounts = set(old_discounts) - set(new_discounts)
        changed_discounts = {code for code in old_discounts if
                             code in new_discounts and old_discounts[code] != new_discounts[code]}

        if added_discounts or removed_discounts or changed_discounts:
            updated_fields.append("discounts")

        return PlanUpdated(id=new_plan.id, updated_at=new_plan.updated_at, updated_fields=updated_fields)
