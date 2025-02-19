from copy import copy, deepcopy
from datetime import timedelta
from enum import StrEnum
from typing import Optional, Self
from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.eventable import (Eventable, Property)
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import (
    SubscriptionPaused, SubscriptionResumed, SubscriptionRenewed,
    SubscriptionExpired, SubId)
from backend.subscription.domain.item_manager import ItemManager
from backend.subscription.domain.plan import PlanId, Plan
from backend.subscription.domain.usage import Usage


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
    autorenew: bool = Property(default=False)
    fields: dict = Property(default_factory=dict)
    id: SubId = Property(frozen=True, default_factory=uuid4)
    discounts: ItemManager[Discount] = Property(frozen=True, mapper=ItemManager)
    usages: ItemManager[Usage] = Property(frozen=True, mapper=ItemManager)
    created_at: AwareDatetime = Property(frozen=True, default_factory=get_current_datetime)
    updated_at: AwareDatetime = Property(frozen=True, default_factory=get_current_datetime)

    _status: SubscriptionStatus = SubscriptionStatus.Active
    _paused_from: Optional[AwareDatetime] = None

    @property
    def status(self):
        return self._status

    @property
    def paused_from(self):
        return self._paused_from

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
        instance = cls(plan_info=plan_info, billing_info=billing_info, subscriber_id=subscriber_id, auth_id=auth_id,
                       autorenew=autorenew, usages=usages, discounts=discounts, fields=fields, id=id)
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
        return cls(plan_info=plan_info, billing_info=billing_info, subscriber_id=subscriber_id, auth_id=plan.auth_id,
                   autorenew=False, usages=usages, discounts=discounts)

    def pause(self) -> None:
        if self.status == SubscriptionStatus.Paused:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot pause the subscription with 'Expired' status")
        self._status = SubscriptionStatus.Paused
        self._paused_from = get_current_datetime()
        self.push_event(
            SubscriptionPaused(subscription_id=self.id, paused_from=self.paused_from, auth_id=self.auth_id)
        )

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

        self.push_event(
            SubscriptionResumed(subscription_id=self.id, auth_id=self.auth_id)
        )

    def renew(self, from_date: AwareDatetime = None) -> None:
        if self.status != SubscriptionStatus.Expired:
            raise ValueError(f"Cannot resume the subscription with {self.status} status")
        if from_date is None:
            from_date = get_current_datetime()

        self._status = SubscriptionStatus.Active
        self.billing_info.last_billing = from_date
        self._paused_from = None

        self.push_event(
            SubscriptionRenewed(subscription_id=self.id, auth_id=self.auth_id, last_billing=from_date)
        )

    def expire(self) -> None:
        self._status = SubscriptionStatus.Expired
        self.push_event(
            SubscriptionExpired(subscription_id=self.id, auth_id=self.auth_id)
        )

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
