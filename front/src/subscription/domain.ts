
export enum Period {
    Daily = "daily",
    Weekly = "weekly",
    Monthly = "monthly",
    Quarterly = "quarterly",
    Semiannual = "semiannual",
    Annual = "annual",
    Lifetime = "lifetime",
}

export enum SubscriptionStatus {
    Active = "active",
    Paused = "paused",
    Expired = "expired"
}


export interface UsageRate {
    title: string
    code: string
    unit: string
    availableUnits: number
    renewCycle: Period
}

export interface Usage extends UsageRate {
    usedUnits: number
    lastRenew: Date
}


export interface Discount {
    title: string
    code: string
    description?: string
    size: number
    validUntil: Date
}

export interface Plan {
    id: string
    title: string
    price: number
    currency: string
    billingCycle: Period
    description?: string
    level: number
    features: string
    usageRates: UsageRate[]
    fields: Record<string, any>
    discounts: Discount[]
    createdAt: Date
    updatedAt: Date
}

export interface PlanCU {
    id: string
    title: string
    price: number
    currency: string
    billingCycle: Period,
    description?: string
    level: number
    features?: string
    usageRates: UsageRate[]
    fields: Record<string, any>
    discounts: Discount[]
}

export interface PlanInfo {
    id: string
    title: string
    description: string | null | undefined
    level: number
    features: string
}

export interface BillingInfo {
    price: number
    currency: string
    billingCycle: Period
    lastBilling: Date
    savedDays: number
}

export interface Subscription {
    id: string
    subscriberId: string
    planInfo: PlanInfo
    billingInfo: BillingInfo
    status: SubscriptionStatus
    pausedFrom?: Date | null
    usages: Usage[]
    discounts: Discount[]
    fields: Record<string, any>
    createdAt: Date
    updatedAt: Date
}

export interface SubscriptionCU {
    id: string
    subscriberId: string
    planInfo: PlanInfo
    billingInfo: BillingInfo
    status: SubscriptionStatus
    pausedFrom?: Date | null
    usages: Usage[]
    discounts: Discount[]
    fields?: Record<string, any>
}
