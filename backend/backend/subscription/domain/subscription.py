from copy import copy, deepcopy
from datetime import timedelta
from enum import StrEnum
from typing import Optional, Self, Callable
from uuid import UUID, uuid4

from loguru import logger
from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import (Event, ItemAdded, ItemRemoved, ItemUpdated,
                                                    FieldUpdated)
from backend.shared.event_driven.eventable import (Eventable, EventableSet)
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import PlanId, Plan
from backend.subscription.domain.usage import Usage

SubId = UUID


class PlanInfo(Eventable):
    id: PlanId
    title: str
    description: Optional[str]
    level: int
    features: Optional[str]


class BillingInfo(Eventable):
    price: float
    currency: str
    billing_cycle: Period
    last_billing: AwareDatetime


class SubscriptionStatus(StrEnum):
    Active = "active"
    Paused = "paused"
    Expired = "expired"


class Subscription(Eventable):
    plan_info: PlanInfo
    billing_info: BillingInfo
    subscriber_id: str
    auth_id: AuthId
    autorenew: bool
    fields: dict

    _id: SubId
    _status: SubscriptionStatus
    _paused_from: Optional[AwareDatetime]
    _discounts: EventableSet[Discount]
    _usages: EventableSet[Usage]
    _created_at: AwareDatetime
    _updated_at: AwareDatetime

    def __init__(
            self,
            plan_info: PlanInfo,
            billing_info: BillingInfo,
            subscriber_id: str,
            auth_id: AuthId,
            autorenew: bool = False,
            usages: list[Usage] = None,
            discounts: list[Discount] = None,
            fields: dict = None,
            id: SubId = None,
    ):
        dt = get_current_datetime()
        data = {
            "plan_info": plan_info,
            "billing_info": billing_info,
            "subscriber_id": subscriber_id,
            "auth_id": auth_id,
            "autorenew": autorenew,
            "fields": fields if fields is not None else {},
            "_id": id if id else uuid4(),
            "_status": SubscriptionStatus.Active,
            "_paused_from": None,
            "_created_at": dt,
            "_updated_at": dt,
            "_usages": EventableSet(usages, lambda x: x.code, True),
            "_discounts": EventableSet(discounts, lambda x: x.code, True),
        }
        super().__init__(**data)

    @property
    def id(self):
        return self._id

    @property
    def status(self):
        return self._status

    @property
    def paused_from(self):
        return self._paused_from

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at

    @property
    def usages(self) -> EventableSet[Usage]:
        return self._usages

    @property
    def discounts(self) -> EventableSet[Discount]:
        return self._discounts

    @classmethod
    def create_unsafe(
            cls,
            id: SubId,
            plan_info: PlanInfo,
            billing_info: BillingInfo,
            subscriber_id: str,
            auth_id: AuthId,
            status: SubscriptionStatus,
            paused_from: Optional[AwareDatetime],
            created_at: AwareDatetime,
            updated_at: AwareDatetime,
            autorenew: bool,
            usages: list[Usage],
            discounts: list[Discount],
            fields: dict,
    ):
        instance = cls(plan_info, billing_info, subscriber_id, auth_id, autorenew, usages, discounts, fields, id)
        instance.__setuntrack__("_status", status)
        instance.__setuntrack__("_paused_from", paused_from)
        instance.__setuntrack__("_created_at", created_at)
        instance.__setuntrack__("_updated_at", updated_at)
        return instance

    @classmethod
    def from_plan(cls, plan: Plan, subscriber_id: str) -> Self:
        dt = get_current_datetime()
        plan_info = PlanInfo(id=plan.id, title=plan.title, description=plan.description, level=plan.level,
                             features=plan.features)
        billing_info = BillingInfo(price=plan.price, currency=plan.currency, billing_cycle=plan.billing_cycle,
                                   last_billing=dt)
        discounts = plan.discounts.get_all().copy()
        usages = [Usage.from_usage_rate(rate) for rate in plan.usage_rates]
        return cls(plan_info, billing_info, subscriber_id, plan.auth_id, False, usages, discounts)

    def pause(self) -> None:
        if self.status == SubscriptionStatus.Paused:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot pause the subscription with 'Expired' status")
        self._status = SubscriptionStatus.Paused
        self._paused_from = get_current_datetime()
        self.push_event(SubscriptionPaused(subscription_id=self.id, paused_from=self.paused_from, auth_id=self.auth_id,
                                           occurred_at=get_current_datetime()))

    def resume(self) -> None:
        if self.status == SubscriptionStatus.Active:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot resume the subscription with 'Expired' status")

        last_billing = self.billing_info.last_billing
        if self.status == SubscriptionStatus.Paused:
            saved_days = get_current_datetime() - self.paused_from
            last_billing = self.billing_info.last_billing + saved_days

        self._status = SubscriptionStatus.Active
        self._paused_from = None
        self.billing_info.last_billing = last_billing

    def renew(self, from_date: AwareDatetime = None) -> None:
        if self.status == SubscriptionStatus.Paused:
            raise ValueError("Cannot resume the subscription with 'Paused' status")
        if from_date is None:
            from_date = get_current_datetime()

        self._status = SubscriptionStatus.Active
        self.billing_info.last_billing = from_date
        self._paused_from = None

    def expire(self) -> None:
        self._status = SubscriptionStatus.Expired

    @property
    def days_left(self) -> int:
        billing_days = self.billing_info.billing_cycle.get_cycle_in_days()
        if self.status == SubscriptionStatus.Paused:
            saved_days = (get_current_datetime() - self.paused_from).days
            return (self.billing_info.last_billing + timedelta(
                days=saved_days + billing_days) - get_current_datetime()).days
        days_left = (self.billing_info.last_billing + timedelta(days=billing_days) - get_current_datetime()).days
        return days_left if days_left > 0 else 0

    @property
    def expiration_date(self):
        saved_days = (get_current_datetime() - self.paused_from).days if self.status == SubscriptionStatus.Paused else 0
        days_delta = saved_days + self.billing_info.billing_cycle.get_cycle_in_days()
        return self.billing_info.last_billing + timedelta(days=days_delta)

    def copy(self, deep=False) -> Self:
        return deepcopy(deep) if deep else copy(self)

    def parse_events(self) -> list[Event]:
        events = super().parse_events()
        parser = SubscriptionEventParser(self)
        return parser.parse(events)


class SubscriptionEventParser:
    def __init__(self, subscription: Subscription):
        self.subscription = subscription
        self.updated_fields = set()
        self.result = []
        self.dt = get_current_datetime()

    def parse(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._handle_event(event)

        if self.updated_fields:
            self.result.append(
                SubscriptionUpdated(
                    subscription_id=self.subscription.id,
                    changed_fields=tuple(self.updated_fields),
                    auth_id=self.subscription.auth_id,
                    occurred_at=self.dt
                )
            )
        return self.result

    def _handle_event(self, event):
        event_handlers = {
            FieldUpdated: self._handle_field_updated,
            ItemAdded: self._handle_item_added,
            ItemUpdated: self._handle_item_updated,
            ItemRemoved: self._handle_item_removed
        }

        handler: Callable = event_handlers.get(type(event))
        if handler:
            handler(event)
        else:
            self.result.append(event)

    def _handle_field_updated(self, event: FieldUpdated):
        entity_field_map = {
            Subscription: "{key}",
            Usage: "usages.{key}:updated",
            Discount: "discounts.{key}:updated",
            BillingInfo: "billing_info.{key}",
            PlanInfo: "plan_info.{key}"
        }

        key = event.field.lstrip("_")
        entity_type = type(event.entity)
        try:
            field_template = entity_field_map[entity_type]
            self.updated_fields.add(field_template.format(key=key))
        except KeyError:
            raise TypeError(entity_type)

    def _handle_item_added(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields.add(f"usages.{event.item.code}:added")
            self.result.append(
                SubscriptionUsageAdded(
                    subscription_id=self.subscription.id, code=event.item.code, unit=event.item.unit,
                    available_units=event.item.available_units, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields.add(f"discounts.{event.item.code}:added")
            self.result.append(
                SubscriptionDiscountAdded(
                    subscription_id=self.subscription.id, title=event.item.title, code=event.item.code,
                    size=event.item.size, valid_until=event.item.valid_until, description=event.item.description,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_updated(self, event):
        if isinstance(event.new_item, Usage):
            self.updated_fields.add(f"usages.{event.new_item.code}:updated")
            self.result.append(
                SubscriptionUsageUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    unit=event.new_item.unit, available_units=event.new_item.available_units,
                    used_units=event.new_item.used_units,
                    delta=event.new_item.used_units - event.old_item.used_units,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.new_item, Discount):
            self.updated_fields.add(f"discounts.{event.new_item.code}:updated")
            self.result.append(
                SubscriptionDiscountUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    size=event.new_item.size, valid_until=event.new_item.valid_until,
                    description=event.new_item.description, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_removed(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields.add(f"usages.{event.item.code}:removed")
            self.result.append(
                SubscriptionUsageRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields.add(f"discounts.{event.item.code}:removed")
            self.result.append(
                SubscriptionDiscountRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
            )


class SubscriptionUpdatesEventGenerator:
    def __init__(self, old_subscription: Subscription, new_subscription: Subscription):
        self.old_subscription = old_subscription
        self.new_subscription = new_subscription
        self.events = []
        self.now = get_current_datetime()

    def generate_events(self) -> list[Event]:
        self.now = get_current_datetime()
        self._check_status_change()
        self._check_discounts()
        self._check_usages()
        self._check_general_updates()
        events = self.events
        self.events = []
        return events

    def _check_status_change(self):
        if self.old_subscription.status != self.new_subscription.status:
            if self.new_subscription.status == SubscriptionStatus.Paused:
                self.events.append(
                    SubscriptionPaused(subscription_id=self.new_subscription.id, auth_id=self.new_subscription.auth_id,
                                       occurred_at=self.now, paused_from=self.new_subscription.paused_from)
                )
            elif self.new_subscription.status == SubscriptionStatus.Active:
                if self.old_subscription.status == SubscriptionStatus.Expired:
                    self.events.append(
                        SubscriptionRenewed(subscription_id=self.new_subscription.id,
                                            auth_id=self.new_subscription.auth_id, occurred_at=self.now,
                                            last_billing=self.new_subscription.billing_info.last_billing)
                    )
                elif self.old_subscription.status == SubscriptionStatus.Paused:
                    self.events.append(
                        SubscriptionResumed(subscription_id=self.new_subscription.id,
                                            auth_id=self.new_subscription.auth_id, occurred_at=self.now)
                    )
                else:
                    raise ValueError
            elif self.new_subscription.status == SubscriptionStatus.Expired:
                self.events.append(
                    SubscriptionExpired(subscription_id=self.new_subscription.id, auth_id=self.new_subscription.auth_id,
                                        occurred_at=self.now))

    def _check_discounts(self):
        old_discounts = {d.code: d for d in self.old_subscription.discounts}
        new_discounts = {d.code: d for d in self.new_subscription.discounts}

        for code, new_discount in new_discounts.items():
            if code not in old_discounts:
                self.events.append(
                    SubscriptionDiscountAdded(subscription_id=self.new_subscription.id, title=new_discount.title,
                                              code=new_discount.code, size=new_discount.size,
                                              valid_until=new_discount.valid_until,
                                              description=new_discount.description,
                                              auth_id=self.new_subscription.auth_id, occurred_at=self.now))
            elif old_discounts[code] != new_discount:
                self.events.append(
                    SubscriptionDiscountUpdated(subscription_id=self.new_subscription.id, title=new_discount.title,
                                                code=new_discount.code, size=new_discount.size,
                                                valid_until=new_discount.valid_until,
                                                description=new_discount.description,
                                                auth_id=self.new_subscription.auth_id, occurred_at=self.now))

        for code in old_discounts:
            if code not in new_discounts:
                self.events.append(SubscriptionDiscountRemoved(subscription_id=self.new_subscription.id, code=code,
                                                               auth_id=self.new_subscription.auth_id,
                                                               occurred_at=self.now))

    def _check_usages(self):
        old_usages = {u.code: u for u in self.old_subscription.usages}
        new_usages = {u.code: u for u in self.new_subscription.usages}

        for code, new_usage in new_usages.items():
            if code not in old_usages:
                self.events.append(SubscriptionUsageAdded(subscription_id=self.new_subscription.id, code=new_usage.code,
                                                          unit=new_usage.unit,
                                                          available_units=new_usage.available_units,
                                                          auth_id=self.new_subscription.auth_id, occurred_at=self.now))
            else:
                old_usage = old_usages[code]
                if old_usage.available_units != new_usage.available_units or old_usage.used_units != new_usage.used_units:
                    delta = new_usage.used_units - old_usage.used_units
                    self.events.append(
                        SubscriptionUsageUpdated(subscription_id=self.new_subscription.id, title=new_usage.title,
                                                 code=new_usage.code, unit=new_usage.unit,
                                                 available_units=new_usage.available_units,
                                                 used_units=new_usage.used_units, delta=delta,
                                                 auth_id=self.new_subscription.auth_id, occurred_at=self.now))

        for code in old_usages:
            if code not in new_usages:
                self.events.append(SubscriptionUsageRemoved(subscription_id=self.new_subscription.id, code=code,
                                                            auth_id=self.new_subscription.auth_id,
                                                            occurred_at=self.now))

    def _check_general_updates(self):
        changed_fields = []
        for field in ['plan_info.id', 'plan_info.title', 'plan_info.description', 'plan_info.level',
                      'plan_info.features', 'billing_info.price', 'billing_info.currency', 'billing_info.last_billing',
                      'billing_info.billing_cycle', 'status', 'paused_from', 'subscriber_id', 'autorenew', 'fields',
                      ]:
            old_value = eval(f'self.old_subscription.{field}')
            new_value = eval(f'self.new_subscription.{field}')
            if old_value != new_value:
                changed_fields.append(field)

        old_discounts = {d.code for d in self.old_subscription.discounts}
        new_discounts = {d.code for d in self.new_subscription.discounts}

        for code in new_discounts - old_discounts:
            changed_fields.append(f'discounts.{code}:added')
        for code in old_discounts - new_discounts:
            changed_fields.append(f'discounts.{code}:removed')
        for code in old_discounts.intersection(new_discounts):
            if self.old_subscription.discounts.get(code) != self.new_subscription.discounts.get(code):
                changed_fields.append(f'discounts.{code}:updated')

        old_usages = {u.code for u in self.old_subscription.usages}
        new_usages = {u.code for u in self.new_subscription.usages}

        for code in new_usages - old_usages:
            changed_fields.append(f'usages.{code}:added')
        for code in old_usages - new_usages:
            changed_fields.append(f'usages.{code}:removed')
        for code in old_usages.intersection(new_usages):
            if self.old_subscription.usages.get(code) != self.new_subscription.usages.get(code):
                changed_fields.append(f'usages.{code}:updated')

        if changed_fields:
            self.events.append(
                SubscriptionUpdated(subscription_id=self.new_subscription.id, changed_fields=tuple(changed_fields),
                                    auth_id=self.new_subscription.auth_id, occurred_at=self.now)
            )


class SubscriptionCreated(Event):
    subscription_id: SubId
    price: float
    currency: str
    billing_cycle: Period
    usage_codes: tuple[str]
    discount_codes: tuple[str]
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionDeleted(Event):
    subscription_id: SubId
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionPaused(Event):
    subscription_id: SubId
    paused_from: AwareDatetime
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionResumed(Event):
    subscription_id: SubId
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionRenewed(Event):
    subscription_id: SubId
    last_billing: AwareDatetime
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionExpired(Event):
    subscription_id: SubId
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionUsageAdded(Event):
    subscription_id: SubId
    code: str
    unit: str
    available_units: float
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionUsageRemoved(Event):
    subscription_id: SubId
    code: str
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionUsageUpdated(Event):
    subscription_id: SubId
    title: str
    code: str
    unit: str
    available_units: float
    used_units: float
    delta: float
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionDiscountAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    size: float
    valid_until: AwareDatetime
    description: str
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionDiscountRemoved(Event):
    subscription_id: SubId
    code: str
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionDiscountUpdated(Event):
    subscription_id: SubId
    title: str
    code: str
    size: float
    valid_until: AwareDatetime
    description: str
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionUpdated(Event):
    subscription_id: SubId
    changed_fields: tuple[str, ...]
    auth_id: AuthId
    occurred_at: AwareDatetime
