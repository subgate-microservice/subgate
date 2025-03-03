import {
    BillingInfo,
    Discount,
    Period,
    PlanInfo,
    Subscription,
    SubscriptionUpdate,
    SubscriptionStatus,
    Usage, UsageRate, PlanCU
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
        renewCycle: Period.Lifetime,
    }
}

export function blankPlanCU(): PlanCU {
    return {
        id: v4(),
        title: "",
        price: 0,
        currency: "USD",
        billingCycle: Period.Monthly,
        description: "",
        level: 10,
        features: "",
        usageRates: [],
        fields: {},
        discounts: [],
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
        billingCycle: Period.Monthly,
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

export function blankSubscriptionCU(): SubscriptionUpdate {
    return {
        id: v4(),
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