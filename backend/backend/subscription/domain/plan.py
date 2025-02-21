from copy import copy
from typing import Any, Optional, Self
from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.eventable import Eventable, EventableSet, Property
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import PlanId, PlanUpdated, PlanDeleted, PlanCreated
from backend.subscription.domain.usage import UsageRate


class Plan(Eventable):
    title: str
    price: float
    currency: str
    auth_id: AuthId
    billing_cycle: Period
    description: Optional[str]
    level: int
    features: Optional[str]
    fields: dict
    id: PlanId = Property(frozen=True)
    usage_rates: EventableSet[UsageRate] = Property(frozen=True)
    discounts: EventableSet[Discount] = Property(frozen=True)
    created_at: AwareDatetime = Property(frozen=True)
    updated_at: AwareDatetime = Property(frozen=True)

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
        dt = get_current_datetime()
        data = {
            "title": title,
            "price": price,
            "currency": currency,
            "auth_id": auth_id,
            "billing_cycle": billing_cycle,
            "description": description,
            "level": level,
            "features": features,
            "fields": fields if fields is not None else {},
            "id": id if id else uuid4(),
            "usage_rates": EventableSet(usage_rates, lambda x: x.code, True),
            "discounts": EventableSet(discounts, lambda x: x.code, True),
            "created_at": dt,
            "updated_at": dt,
        }
        super().__init__(**data)

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

    def copy(self):
        return copy(self)


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
        return PlanDeleted(id=self.plan.id, auth_id=self.plan.auth_id, deleted_at=dt)

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

        return PlanUpdated(id=new_plan.id, updated_at=new_plan.updated_at, updated_fields=updated_fields,
                           auth_id=new_plan.auth_id)
