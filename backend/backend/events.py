from backend.subscription.domain.plan import PlanCreated, PlanUpdated, PlanDeleted
from backend.subscription.domain.subscription import (
    SubscriptionPaused, SubscriptionUpdated, SubscriptionUsageAdded, SubscriptionResumed, SubscriptionUsageUpdated,
    SubscriptionUsageRemoved, SubscriptionDiscountUpdated, SubscriptionDiscountAdded, SubscriptionDiscountRemoved,
    SubscriptionRenewed, SubscriptionCreated, SubscriptionDeleted,
)

EVENTS = [
    PlanCreated,
    PlanUpdated,
    PlanDeleted,

    SubscriptionCreated,
    SubscriptionUpdated,
    SubscriptionDeleted,

    SubscriptionPaused,
    SubscriptionResumed,
    SubscriptionRenewed,

    SubscriptionUsageAdded,
    SubscriptionUsageUpdated,
    SubscriptionUsageRemoved,

    SubscriptionDiscountAdded,
    SubscriptionDiscountUpdated,
    SubscriptionDiscountRemoved,
]
