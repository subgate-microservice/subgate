from enum import StrEnum


class EventCode(StrEnum):
    SubscriptionCreated = "SubscriptionCreated"
    SubscriptionUpdated = "SubscriptionUpdated"
    SubscriptionDeleted = "SubscriptionDeleted"
    SubscriptionExpired = "SubscriptionExpired"
    SubscriptionPaused = "SubscriptionPaused"
    SubscriptionResumed = "SubscriptionResumed"
    SubscriptionRenewed = "SubscriptionRenewed"
    LastBillingChanged = "LastBillingChanged"
    ActiveSubscriptionChanged = "ActiveSubscriptionChanged"
    PlanCreated = "PlanCreated"
    PlanUpdated = "PlanUpdated"
    PlanDeleted = "PlanDeleted"
