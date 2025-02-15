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


class PlanCreated(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    created_at: AwareDatetime


class PlanDeleted(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    deleted_at: AwareDatetime


class PlanUpdated(Event):
    id: PlanId
    updated_at: AwareDatetime
    updated_fields: list[str]


class Plan:
    def __init__(
            self,
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
    ):
        self.title = title
        self.price = price
        self.currency = currency
        self.billing_cycle = billing_cycle
        self.description = description
        self.level = level
        self.features = features
        self.fields = fields if fields is not None else {}
        self.auth_id = auth_id

        self._id = id if id else uuid4()
        self._usage_rates = ItemManager(usage_rates, lambda x: x.code)
        self._discounts = ItemManager(discounts, lambda x: x.code)
        self._created_at = get_current_datetime()
        self._updated_at = self.created_at

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
    def create_unsafe(
            cls,
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
    ) -> Self:
        instance = cls(title, price, currency, auth_id, billing_cycle, description, level, features, usage_rates,
                       discounts,
                       fields, id)
        instance._created_at = created_at
        instance._updated_at = updated_at
        return instance


class PlanEventFactory:
    def __init__(self, plan: Plan):
        self.plan = plan

    def plan_created(self) -> PlanCreated:
        return PlanCreated(
            id=self.plan.id, title=self.plan.title, price=self.plan.price, currency=self.plan.currency,
            billing_cycle=self.plan.billing_cycle, auth_id=self.plan.auth_id, created_at=self.plan.created_at
        )

    def plan_deleted(self) -> PlanDeleted:
        dt = get_current_datetime()
        return PlanDeleted(
            id=self.plan.id, title=self.plan.title, price=self.plan.price, currency=self.plan.currency,
            billing_cycle=self.plan.billing_cycle, auth_id=self.plan.auth_id, deleted_at=dt
        )

    def plan_updated(self, new_plan: Plan) -> PlanUpdated:
        old_plan = self.plan
        updated_fields = []

        # Проверяем простые атрибуты
        for field in (
                "title", "price", "currency", "billing_cycle", "description", "level", "features", "fields",
                "auth_id"
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
