from typing import Optional, Any
from uuid import UUID

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.enums import UnionValue
from backend.shared.event_driven.base_event import Event
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.enums import SubscriptionStatus

SubId = UUID
PlanId = UUID


class PlanCreated(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId


class PlanDeleted(PlanCreated):
    pass


class PlanUpdated(Event):
    id: PlanId
    changes: dict[str, UnionValue]
    auth_id: AuthId


class SubCreated(Event):
    id: SubId
    subscriber_id: str
    status: SubscriptionStatus
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId


class SubDeleted(SubCreated):
    pass


class SubUpdated(Event):
    id: SubId
    subscriber_id: str
    changes: dict[str, Any]
    auth_id: AuthId


class SubPaused(Event):
    id: SubId
    subscriber_id: str
    auth_id: AuthId


class SubResumed(SubPaused):
    saved_days: int


class SubExpired(SubPaused):
    pass


class SubRenewed(Event):
    id: SubId
    subscriber_id: str
    last_billing: AwareDatetime
    auth_id: AuthId


class SubUsageAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    used_units: float
    last_renew: AwareDatetime
    auth_id: AuthId


class SubUsageUpdated(Event):
    subscription_id: SubId
    code: str
    changes: dict[str, UnionValue]
    delta: float
    auth_id: AuthId


class SubUsageRemoved(SubUsageAdded):
    pass


class SubDiscountAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: AwareDatetime
    auth_id: AuthId


class SubDiscountRemoved(SubDiscountAdded):
    pass


class SubDiscountUpdated(Event):
    subscription_id: SubId
    code: str
    changes: dict[str, UnionValue]
    auth_id: AuthId
