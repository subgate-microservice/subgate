from typing import Optional
from uuid import UUID

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import Event
from backend.subscription.domain.cycle import Period

SubId = UUID


class SubscriptionCreated(Event):
    id: SubId
    subscriber_id: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId


class SubscriptionDeleted(SubscriptionCreated):
    pass


class SubscriptionUpdated(Event):
    id: SubId
    subscriber_id: SubId
    changed_fields: tuple[str, ...]
    auth_id: AuthId


class SubscriptionPaused(Event):
    id: SubId
    subscriber_id: str
    paused_from: AwareDatetime
    auth_id: AuthId


class SubscriptionResumed(Event):
    id: SubId
    subscriber_id: str
    last_billing: AwareDatetime
    auth_id: AuthId


class SubscriptionRenewed(Event):
    id: SubId
    subscriber_id: str
    last_billing: AwareDatetime
    auth_id: AuthId


class SubscriptionExpired(Event):
    id: SubId
    subscriber_id: str
    auth_id: AuthId


class SubscriptionUsageAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    used_units: float
    last_renew: AwareDatetime
    auth_id: AuthId


class SubscriptionUsageUpdated(SubscriptionUsageAdded):
    delta: float


class SubscriptionUsageRemoved(SubscriptionUsageAdded):
    pass


class SubscriptionDiscountAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: AwareDatetime
    auth_id: AuthId


class SubscriptionDiscountRemoved(SubscriptionDiscountAdded):
    pass


class SubscriptionDiscountUpdated(SubscriptionDiscountAdded):
    pass
