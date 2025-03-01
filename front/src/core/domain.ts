import {z} from "zod";

export const Period = z.enum([
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "semiannual",
    "annual",
    "lifetime",
])
export type Period = z.infer<typeof Period>


export interface UsageRate{
    title: string
    code: string
    unit: string
    availableUnits: number
    renewCycle: Period
}

export interface Discount{
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

export interface PlanCreate{
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

export interface PlanUpdate extends PlanCreate{
    id: string
}
