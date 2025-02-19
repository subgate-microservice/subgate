from typing import Optional
from uuid import UUID

from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.event_driven.base_event import Event
from backend.subscription.domain.cycle import Period

SubId = UUID


class SubscriptionCreated(Event):
    subscription_id: SubId
    price: float
    currency: str
    billing_cycle: Period
    usage_codes: tuple[str, ...]
    discount_codes: tuple[str, ...]
    auth_id: AuthId


class SubscriptionDeleted(Event):
    subscription_id: SubId
    auth_id: AuthId


class SubscriptionPaused(Event):
    subscription_id: SubId
    paused_from: AwareDatetime
    auth_id: AuthId


class SubscriptionResumed(Event):
    subscription_id: SubId
    auth_id: AuthId


class SubscriptionRenewed(Event):
    subscription_id: SubId
    last_billing: AwareDatetime
    auth_id: AuthId


class SubscriptionExpired(Event):
    subscription_id: SubId
    auth_id: AuthId


class SubscriptionUsageAdded(Event):
    subscription_id: SubId
    code: str
    unit: str
    available_units: float
    auth_id: AuthId


class SubscriptionUsageRemoved(Event):
    subscription_id: SubId
    code: str
    auth_id: AuthId


class SubscriptionUsageUpdated(Event):
    subscription_id: SubId
    title: str
    code: str
    unit: str
    available_units: float
    used_units: float
    delta: float
    auth_id: AuthId


class SubscriptionDiscountAdded(Event):
    subscription_id: SubId
    title: str
    code: str
    size: float
    valid_until: AwareDatetime
    description: Optional[str]
    auth_id: AuthId


class SubscriptionDiscountRemoved(Event):
    subscription_id: SubId
    code: str
    auth_id: AuthId


class SubscriptionDiscountUpdated(Event):
    subscription_id: SubId
    title: str
    code: str
    size: float
    valid_until: AwareDatetime
    description: Optional[str]
    auth_id: AuthId


class SubscriptionUpdated(Event):
    subscription_id: SubId
    changed_fields: tuple[str, ...]
    auth_id: AuthId
