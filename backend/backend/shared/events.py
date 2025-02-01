from enum import StrEnum


class EventCode(StrEnum):
    SubscriptionCreated = "subscription_created"
    SubscriptionUpdated = "subscription_updated"
    SubscriptionDeleted = "subscription_deleted"
    SubscriptionExpired = "subscription_expired"
    SubscriptionPaused = "subscription_paused"
    SubscriptionResumed = "subscription_resumed"
    SubscriptionRenewed = "subscription_renewed"
    LastBillingChanged = "last_billing_changed"
    ActiveSubscriptionChanged = "active_subscription_changed"
    PlanCreated = "plan_created"
    PlanUpdated = "plan_updated"
    PlanDeleted = "plan_deleted"
