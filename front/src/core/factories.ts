import {
    BillingInfo,
    Discount,
    Period,
    PlanInfo,
    Subscription,
    SubscriptionCreate,
    SubscriptionStatus,
    Usage, UsageRate
} from "./domain.ts";
import {v4} from "uuid";

export function blankDiscount(): Discount {
    return {
        title: "Black Friday",
        code: "black",
        size: 20,
        validUntil: new Date(),
        description: "Any description",
    }
}

export function blankUsage(): Usage {
    return {
        title: "First",
        code: "first",
        unit: "GB",
        availableUnits: 100,
        lastRenew: new Date(),
        usedUnits: 0,
        renewCycle: Period.enum.lifetime,
    }
}


export function usageFromUsageRate(rate: UsageRate): Usage {
    return {
        title: rate.title,
        code: rate.code,
        unit: rate.unit,
        availableUnits: rate.availableUnits,
        renewCycle: rate.renewCycle,
        lastRenew: new Date(),
        usedUnits: 0,
    }
}

export function blankPlanInfo(): PlanInfo {
    return {
        id: v4(),
        title: "Personal",
        description: "Hello",
        features: "",
        level: 10,
    }
}

export function blankBillingInfo(): BillingInfo {
    return {
        billingCycle: Period.enum.monthly,
        currency: "USD",
        lastBilling: new Date(),
        price: 100,
        savedDays: 0
    }
}

export function blankSubscription(): Subscription {
    return {
        id: "",
        subscriberId: "",
        planInfo: blankPlanInfo(),
        billingInfo: blankBillingInfo(),
        status: SubscriptionStatus.Active,
        pausedFrom: null,
        discounts: [],
        usages: [],
        fields: {},
        autorenew: false,
        createdAt: new Date(),
        updatedAt: new Date(),

    }
}

export function blankSubscriptionCreate(): SubscriptionCreate {
    return {
        subscriberId: "AnySubscriberID",
        planInfo: blankPlanInfo(),
        billingInfo: blankBillingInfo(),
        status: SubscriptionStatus.Active,
        pausedFrom: null,
        discounts: [],
        usages: [],
        fields: {},
        autorenew: false,
    }
}