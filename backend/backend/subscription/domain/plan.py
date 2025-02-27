from copy import copy
from typing import Optional, Callable, Union
from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import Event, FieldUpdated, ItemAdded, ItemUpdated, ItemRemoved
from backend.shared.event_driven.eventable import Eventable, Property
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import PlanUpdated, PlanId
from backend.subscription.domain.item_manager import ItemManager
from backend.subscription.domain.usage import UsageRate


class Plan(Eventable):
    id: PlanId = Property(frozen=True)
    title: str
    price: float
    currency: str
    auth_id: AuthId
    billing_cycle: Period
    description: Optional[str]
    level: int
    features: Optional[str]
    fields: dict
    usage_rates: ItemManager[UsageRate] = Property(frozen=True, mapper=ItemManager)
    discounts: ItemManager[Discount] = Property(frozen=True, mapper=ItemManager)
    created_at: AwareDatetime = Property(frozen=True)
    updated_at: AwareDatetime = Property()

    def __init__(self, title: str, price: float, currency: str, auth_id: AuthId, billing_cycle=Period.Monthly,
                 description: str = None, level: int = 10, features: str = None, fields: dict = None,
                 usage_rates: list[UsageRate] = None, discounts: list[Discount] = None,
                 created_at: AwareDatetime = None, updated_at: AwareDatetime = None, id: PlanId = None):
        created_at = created_at if created_at else get_current_datetime()
        updated_at = updated_at if updated_at else created_at
        id = id if id else uuid4()
        super().__init__(title=title, price=price, currency=currency, auth_id=auth_id, billing_cycle=billing_cycle,
                         description=description, level=level, features=features, fields=fields,
                         usage_rates=usage_rates, discounts=discounts, created_at=created_at, updated_at=updated_at,
                         id=id)

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
            ItemAdded: self._handle_item_added,
            ItemUpdated: self._handle_item_updated,
            ItemRemoved: self._handle_item_removed,
        }

        handler: Callable = event_handlers.get(type(event))
        if handler:
            handler(event)
        else:
            self.result.append(event)

    def _handle_field_updated(self, event: FieldUpdated):
        entity_field_map = {
            Plan: ("{key}", event.new_value),
            UsageRate: ("usage_rates.{key}", "action:updated"),
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

    def _handle_item_added(self, event: ItemAdded):
        field = self.get_field_name(event.item)
        self.updated_fields[f"{field}.{event.item.code}"] = "action:added"

    def _handle_item_updated(self, event: ItemUpdated):
        field = self.get_field_name(event.new_item)
        self.updated_fields[f"{field}.{event.new_item.code}"] = "action:updated"

    def _handle_item_removed(self, event: ItemAdded):
        field = self.get_field_name(event.item)
        self.updated_fields[f"{field}.{event.item.code}"] = "action:removed"

    @staticmethod
    def get_field_name(item: Union[UsageRate, Discount]):
        if isinstance(item, UsageRate):
            field = "usage_rates"
        elif isinstance(item, Discount):
            field = "discounts"
        else:
            raise TypeError(type(item))
        return field
