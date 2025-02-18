from backend.subscription.domain.plan import PlanCreated, PlanUpdated, PlanDeleted
from backend.subscription.domain.events import SubscriptionCreated, SubscriptionDeleted, SubscriptionPaused, \
    SubscriptionResumed, SubscriptionRenewed, SubscriptionUsageAdded, SubscriptionUsageRemoved, \
    SubscriptionUsageUpdated, SubscriptionDiscountAdded, SubscriptionDiscountRemoved, SubscriptionDiscountUpdated, \
    SubscriptionUpdated

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
