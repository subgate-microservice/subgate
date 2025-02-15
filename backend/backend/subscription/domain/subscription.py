import dataclasses
from copy import copy
from datetime import timedelta
from enum import StrEnum
from typing import Optional, Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import Event
from backend.shared.item_maanger import ItemManager
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import PlanId, Plan
from backend.subscription.domain.usage import Usage

SubId = UUID


@dataclasses.dataclass()
class PlanInfo:
    id: PlanId
    title: str
    description: Optional[str]
    level: int
    features: Optional[str]


@dataclasses.dataclass()
class BillingInfo:
    price: float
    currency: str
    billing_cycle: Period
    last_billing: AwareDatetime


class SubscriptionStatus(StrEnum):
    Active = "active"
    Paused = "paused"
    Expired = "expired"


class Subscription:
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
        self._id = id if id else uuid4()
        self._status = SubscriptionStatus.Active
        self._paused_from = None
        self._created_at = get_current_datetime()
        self._updated_at = self._created_at
        self._usages = ItemManager(usages, lambda x: x.code)
        self._discounts = ItemManager(discounts, lambda x: x.code)

        self.plan_info = plan_info
        self.billing_info = billing_info
        self.subscriber_id = subscriber_id
        self.auth_id = auth_id
        self.fields = fields if fields is not None else {}
        self.autorenew = autorenew

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
    def usages(self) -> ItemManager[Usage]:
        return self._usages

    @property
    def discounts(self) -> ItemManager[Discount]:
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
        instance._status = status
        instance._paused_from = paused_from
        instance._created_at = created_at
        instance._updated_at = updated_at
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
            raise ValueError("Cannot paused the subscription with 'Expired' status")
        self._status = SubscriptionStatus.Paused
        self._paused_from = get_current_datetime()

    def resume(self) -> None:
        if self.status == SubscriptionStatus.Active:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot resumed the subscription with 'Expired' status")

        last_billing = self.billing_info.last_billing
        if self.status == SubscriptionStatus.Paused:
            saved_days = get_current_datetime() - self.paused_from
            last_billing = self.billing_info.last_billing + saved_days

        self._status = SubscriptionStatus.Active
        self._paused_from = None
        self.billing_info.last_billing = last_billing

    def renew(self, from_date: AwareDatetime = None) -> None:
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

    def copy(self) -> Self:
        return copy(self)


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
    resumed_from: AwareDatetime
    auth_id: AuthId
    occurred_at: AwareDatetime


class SubscriptionRenewed(Event):
    subscription_id: SubId
    renewed_from: AwareDatetime
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
                                       occurred_at=self.now, paused_from=self.new_subscription.paused_from))
            elif self.new_subscription.status == SubscriptionStatus.Active:
                self.events.append(
                    SubscriptionResumed(subscription_id=self.new_subscription.id, auth_id=self.new_subscription.auth_id,
                                        occurred_at=self.now))
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
                      'plan_info.features', 'billing_info.price', 'billing_info.currency',
                      'billing_info.billing_cycle', 'status', 'paused_from', 'subscriber_id', 'autorenew', 'fields'
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

        if changed_fields:
            self.events.append(
                SubscriptionUpdated(subscription_id=self.new_subscription.id, changed_fields=tuple(changed_fields),
                                    auth_id=self.new_subscription.auth_id, occurred_at=self.now))
