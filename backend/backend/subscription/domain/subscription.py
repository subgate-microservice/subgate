from datetime import timedelta
from enum import StrEnum
from typing import Optional, Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.item_maanger import ItemManager
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import PlanId, Plan
from backend.subscription.domain.usage import Usage

SubId = UUID


class PlanInfo(MyBase):
    plan_id: PlanId
    title: str
    description: Optional[str]
    level: int
    features: Optional[str]


class BillingInfo(MyBase):
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
        self._id = id
        self._status = status
        self._paused_from = paused_from
        self._created_at = created_at
        self._updated_at = updated_at
        self._usages = ItemManager(usages, lambda x: x.code)
        self._discounts = ItemManager(discounts, lambda x: x.code)

        self.plan_info = plan_info
        self.billing_info = billing_info
        self.subscriber_id = subscriber_id
        self.auth_id = auth_id
        self.fields = fields
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
    def create(
            cls,
            plan_info: PlanInfo,
            billing_info: BillingInfo,
            subscriber_id: str,
            auth_id: AuthId,
            autorenew: bool = False,
            usages: list[Usage] = None,
            discounts: list[Discount] = None,
            fields: dict = None,
            id: SubId = None,
    ) -> Self:
        id = id if id else uuid4()
        fields = fields if fields is not None else {}
        usages = usages if usages is not None else []
        discounts = discounts if discounts is not None else []
        dt = get_current_datetime()
        return cls(id=id, plan_info=plan_info, subscriber_id=subscriber_id, billing_info=billing_info, auth_id=auth_id,
                   autorenew=autorenew, fields=fields, usages=usages, discounts=discounts,
                   status=SubscriptionStatus.Active, paused_from=None, created_at=dt, updated_at=dt)

    @classmethod
    def from_plan(cls, plan: Plan, subscriber_id: str) -> Self:
        dt = get_current_datetime()
        plan_info = PlanInfo(plan_id=plan.id, title=plan.title, description=plan.description, level=plan.level,
                             features=plan.features)
        billing_info = BillingInfo(price=plan.price, currency=plan.currency, billing_cycle=plan.billing_cycle,
                                   last_billing=dt)

    def pause(self) -> None:
        if self.status == SubscriptionStatus.Paused:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot paused the subscription with 'Expired' status")
        self._status = SubscriptionStatus.Paused
        self._paused_from = get_current_datetime()
        self._updated_at = get_current_datetime()

    def resume(self) -> None:
        if self.status == SubscriptionStatus.Active:
            return None
        if self.status == SubscriptionStatus.Expired:
            raise ValueError("Cannot resumed the subscription with 'Expired' status")

        last_billing = self.plan_info.last_billing
        if self.status == SubscriptionStatus.Paused:
            saved_days = get_current_datetime() - self.paused_from
            last_billing = self.plan_info.last_billing + saved_days

        self._status = SubscriptionStatus.Active
        self._paused_from = None
        self.billing_info.last_billing = last_billing
        self._updated_at = get_current_datetime()

    def renew(self, from_date: AwareDatetime = None) -> None:
        if from_date is None:
            from_date = get_current_datetime()

        self._status = SubscriptionStatus.Active
        self.billing_info.last_billing = from_date
        self._paused_from = None
        self._updated_at = get_current_datetime()

    def expire(self) -> None:
        self._status = SubscriptionStatus.Expired
        self._updated_at = get_current_datetime()

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
