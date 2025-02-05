from datetime import timedelta
from enum import StrEnum
from typing import Optional, Self, Iterable
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime, model_validator

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.exceptions import ItemNotExist, ItemAlreadyExist
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.plan import Plan, Usage, UsageRate

SubId = UUID


class SubscriptionStatus(StrEnum):
    Active = "active"
    Paused = "paused"
    Expired = "expired"


class Subscription(MyBase):
    id: SubId = Field(default_factory=uuid4)
    plan: Plan
    subscriber_id: str
    auth_id: AuthId = Field(exclude=True)
    status: SubscriptionStatus = SubscriptionStatus.Active
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)
    last_billing: AwareDatetime = Field(default_factory=get_current_datetime)
    paused_from: Optional[AwareDatetime] = Field(default=None)
    autorenew: bool = False
    usages: list[Usage] = Field(default_factory=list)
    fields: dict = Field(default_factory=dict)

    def pause(self) -> Self:
        if self.status != SubscriptionStatus.Paused:
            return self.model_copy(update={
                "paused_from": get_current_datetime(),
                "status": SubscriptionStatus.Paused,
                "updated_at": get_current_datetime(),
            })
        return self

    def resume(self) -> Self:
        if self.status == SubscriptionStatus.Active:
            return self
        last_billing = self.last_billing
        if self.status == SubscriptionStatus.Paused:
            saved_days = get_current_datetime() - self.paused_from
            last_billing = self.last_billing + saved_days
        return self.model_copy(update={
            "status": SubscriptionStatus.Active,
            "last_billing": last_billing,
            "paused_from": None,
            "updated_at": get_current_datetime(),
        })

    def renew(self, from_date: AwareDatetime = None) -> Self:
        if from_date is None:
            from_date = get_current_datetime()
        return self.model_copy(update={
            "status": SubscriptionStatus.Active,
            "last_billing": from_date,
            "paused_from": None,
            "updated_at": get_current_datetime(),
        })

    def shift_last_billing(self, days: int) -> Self:
        shifted = self.last_billing + timedelta(days=days)
        return self.model_copy(update={
            "last_billing": shifted,
            "updated_at": get_current_datetime(),
        })

    def expire(self) -> Self:
        return self.model_copy(update={
            "status": SubscriptionStatus.Expired,
            "updated_at": get_current_datetime(),
        })

    def increase_usage(self, code: str, delta: float) -> Self:
        try:
            target_usage = next(x for x in self.usages if x.code == code)
        except StopIteration:
            raise ItemNotExist(
                item_type=Usage,
                lookup_field_key="code",
                lookup_field_value=code,
            )
        updated_usage = target_usage.model_copy(update={
            "used_units": target_usage.used_units + delta,
            "updated_at": get_current_datetime(),
        })
        new_usages = []
        for usage in self.usages:
            if usage.code == updated_usage.code:
                new_usages.append(updated_usage)
            else:
                new_usages.append(usage)
        return self.model_copy(update={
            "usages": new_usages,
            "updated_at": get_current_datetime(),
        })

    def add_usages(self, usages: Iterable[Usage]) -> Self:
        new_usages = [*self.usages, *usages]
        new_plan = self.plan.add_usage_rates([UsageRate.from_usage(x) for x in usages])
        hashes = set()
        for usage in new_usages:
            if usage.code in hashes:
                raise ItemAlreadyExist(item_type=Usage, index_key="code", index_value=usage.code)
            hashes.add(usage.code)
        return self.model_copy(update={
            "usages": new_usages,
            "plan": new_plan,
            "updated_at": get_current_datetime(),
        })

    def remove_usages(self, codes: Iterable[str]) -> Self:
        codes = set(codes)
        new_usages = [usage for usage in self.usages if usage.code not in codes]
        return self.model_copy(update={
            "usages": new_usages,
            "updated_at": get_current_datetime(),
        })

    def update_usages(self, usages: Iterable[Usage]) -> Self:
        updated_usage_rates = []
        hashes = {}
        for updated_usage in usages:
            hashes[updated_usage.code] = updated_usage
            updated_usage_rates.append(UsageRate.from_usage(updated_usage))

        new_usages = []
        for usage in self.usages:
            updated_usage = hashes.pop(usage.code, None)
            if updated_usage:
                new_usages.append(updated_usage)
            else:
                new_usages.append(usage)
        if len(hashes):
            raise ItemNotExist(
                lookup_field_value=next(key for key in hashes.keys()),
                lookup_field_key="code",
                item_type=Usage,
            )
        new_plan = self.plan.update_usage_rates(updated_usage_rates)
        return self.model_copy(update={
            "plan": new_plan,
            "usages": new_usages,
            "updated_at": get_current_datetime(),
        })

    def update_plan(self, plan: Plan) -> Self:
        return self.model_copy(update={
            "plan": plan,
            "updated_at": get_current_datetime(),
        })

    @property
    def days_left(self) -> int:
        billing_days = self.plan.billing_cycle.cycle_in_days
        if self.status == SubscriptionStatus.Paused:
            saved_days = (get_current_datetime() - self.paused_from).days
            return (self.last_billing + timedelta(days=saved_days + billing_days) - get_current_datetime()).days
        days_left = (self.last_billing + timedelta(days=billing_days) - get_current_datetime()).days
        return days_left if days_left > 0 else 0

    @property
    def expiration_date(self):
        saved_days = (get_current_datetime() - self.paused_from).days if self.status == SubscriptionStatus.Paused else 0
        days_delta = saved_days + self.plan.billing_cycle.cycle_in_days
        return self.last_billing + timedelta(days=days_delta)

    @model_validator(mode="after")
    def _validate_status(self) -> Self:
        if self.status == SubscriptionStatus.Paused:
            if self.paused_from is None:
                raise ValueError("If subscription has Paused status then paused_from field should be a datetime value")
        else:
            if self.paused_from is not None:
                raise ValueError("paused_from should be None or subscription status should be Paused")
        return self

    @model_validator(mode="after")
    def _validate_usages(self) -> Self:
        hashes = set()
        for usage in self.usages:
            if usage.code in hashes:
                raise ItemAlreadyExist(item_type=Usage, index_key="code", index_value=usage.code)
            hashes.add(usage.code)
        return self

    @model_validator(mode="after")
    def _validate_other(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at earlier than created_at")
        if self.last_billing < self.created_at:
            raise ValueError("last_billing earlier than created_at")
        return self
