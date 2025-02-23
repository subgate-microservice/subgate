from backend.subscription.domain.events import (
    SubscriptionCreated,
    SubscriptionDeleted,
    SubscriptionPaused,
    SubscriptionResumed,
    SubscriptionRenewed,
    SubscriptionExpired,
    SubscriptionUsageAdded,
    SubscriptionUsageRemoved,
    SubscriptionUsageUpdated,
    SubscriptionDiscountAdded,
    SubscriptionDiscountRemoved,
    SubscriptionDiscountUpdated,
    SubscriptionUpdated,

    PlanCreated,
    PlanUpdated,
    PlanDeleted,
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
    SubscriptionExpired,

    SubscriptionUsageAdded,
    SubscriptionUsageUpdated,
    SubscriptionUsageRemoved,

    SubscriptionDiscountAdded,
    SubscriptionDiscountUpdated,
    SubscriptionDiscountRemoved,
]
