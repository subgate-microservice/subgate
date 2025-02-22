from copy import copy
from typing import Any, Optional, Self, Callable
from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import Event, FieldUpdated
from backend.shared.event_driven.eventable import Eventable, EventableSet, Property
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import PlanUpdated, PlanId
from backend.subscription.domain.usage import Usage, UsageRate


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


class PlanUpdater:
    def __init__(self, target: Plan, new_plan: Plan):
        self.target = target
        self.new_plan = new_plan

    def _update_simple_fields(self):
        new_plan = self.new_plan

        for field in (
                "title", "price", "currency", "billing_cycle", "description", "level", "features", "fields",
                "auth_id"
        ):
            if getattr(self.target, field) != getattr(new_plan, field):
                self.target.__setattr__(field, getattr(new_plan, field))

    def _update_usage_rates(self):
        new_plan = self.new_plan

        old_rates = {u.code: u for u in self.target.usage_rates}
        new_rates = {u.code: u for u in new_plan.usage_rates}

        old_codes = set(old_rates)
        new_codes = set(new_rates)

        added = new_codes - old_codes
        removed = old_codes - new_codes
        currents = new_codes.intersection(old_codes)

        for code in added:
            self.target.usage_rates.add(new_rates[code])

        for code in removed:
            self.target.usage_rates.remove(code)

        for code in currents:
            if old_rates[code] != new_rates[code]:
                self.target.usage_rates.update(new_rates[code])

    def _update_discounts(self):
        new_plan = self.new_plan

        old_discounts = {u.code: u for u in self.target.discounts}
        new_discounts = {u.code: u for u in new_plan.discounts}

        old_codes = set(old_discounts)
        new_codes = set(new_discounts)

        added = new_codes - old_codes
        removed = old_codes - new_codes
        currents = new_codes.intersection(old_codes)

        for code in added:
            self.target.discounts.add(new_discounts[code])

        for code in removed:
            self.target.discounts.remove(code)

        for code in currents:
            if old_discounts[code] != new_discounts[code]:
                self.target.discounts.update(new_discounts[code])

    def update(self):
        self._update_usage_rates()
        self._update_discounts()
        self._update_simple_fields()


class PlanEventParser:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.updated_fields = {}
        self.result = []

    def parse(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._handle_event(event)

        if self.updated_fields:
            self.result.append(
                PlanUpdated(
                    id=self.plan.id,
                    changes=self.updated_fields,
                    auth_id=self.plan.auth_id,
                    occurred_at=get_current_datetime(),
                )
            )
        return self.result

    def _handle_event(self, event):
        event_handlers = {
            FieldUpdated: self._handle_field_updated,
        }

        handler: Callable = event_handlers.get(type(event))
        if handler:
            handler(event)
        else:
            self.result.append(event)

    def _handle_field_updated(self, event: FieldUpdated):
        entity_field_map = {
            Plan: ("{key}", event.new_value),
            Usage: ("usages.{key}", "action:updated"),
            Discount: ("discounts.{key}", "action:updated"),
        }

        key = event.field.lstrip("_")
        entity_type = type(event.entity)
        try:
            field_template, value = entity_field_map[entity_type]
            key = field_template.format(key=key)
            self.updated_fields[key] = value
        except KeyError:
            raise TypeError(entity_type)
