from backend.subscription.domain.events import (
    SubCreated,
    SubDeleted,
    SubPaused,
    SubResumed,
    SubRenewed,
    SubExpired,
    SubUsageAdded,
    SubUsageRemoved,
    SubUsageUpdated,
    SubDiscountAdded,
    SubDiscountRemoved,
    SubDiscountUpdated,
    SubUpdated,

    PlanCreated,
    PlanUpdated,
    PlanDeleted,
)

EVENTS = [
    PlanCreated,
    PlanUpdated,
    PlanDeleted,

    SubCreated,
    SubUpdated,
    SubDeleted,

    SubPaused,
    SubResumed,
    SubRenewed,
    SubExpired,

    SubUsageAdded,
    SubUsageUpdated,
    SubUsageRemoved,

    SubDiscountAdded,
    SubDiscountUpdated,
    SubDiscountRemoved,
]
