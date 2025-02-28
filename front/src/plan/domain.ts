import {z} from "zod";
import {Currency} from "../other/currency";
import {Period} from "../other/billing-cycle";


export const UsageRate = z.object({
    title: z.string(),
    code: z.string(),
    unit: z.string(),
    availableUnits: z.number(),
    renewCycle: Period,
}).strict()


export const Discount = z.object({
    title: z.string(),
    code: z.string(),
    description: z.string().optional().nullable(),
    size: z.number().min(0).max(1),
    validUntil: z.coerce.date(),
}).strict()

export const Plan = z.object({
    id: z.string(),
    title: z.string(),
    price: z.number(),
    currency: Currency,
    billingCycle: Period,
    description: z.string(),
    level: z.number(),
    features: z.string(),
    usageRates: UsageRate.array(),
    fields: z.record(z.any()),
    discounts: Discount.array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()

export const PlanFormData = z.object({
    title: z.string().min(5),
    price: z.number().min(0),
    currency: Currency,
    billingCycle: Period,
    description: z.string(),
    level: z.number().min(1),
    features: z.string(),
    usageRates: UsageRate.array(),
    fields: z.record(z.any()),
    discounts: Discount.array(),
})

export function convertPlanToPlanFormData(plan: Plan): PlanFormData {
    return {
        title: plan.title,
        price: plan.price,
        currency: plan.currency,
        billingCycle: plan.billingCycle,
        description: plan.description,
        level: plan.level,
        features: plan.features,
        usageRates: plan.usageRates,
        discounts: plan.discounts,
        fields: plan.fields,
    }
}

export function convertPlanFormDataToPlan(
    data: PlanFormData,
    planId: string,
    createdAt: Date,
    updatedAt: Date,
): Plan {
    return {
        id: planId,
        title: data.title,
        price: data.price,
        currency: data.currency,
        billingCycle: data.billingCycle,
        description: data.description,
        level: data.level,
        features: data.features,
        usageRates: data.usageRates,
        discounts: data.discounts,
        fields: data.fields,
        createdAt,
        updatedAt,
    }
}


export interface PlanSby {
    ids?: string[],
}

export type Plan = z.infer<typeof Plan>
export type UsageRate = z.infer<typeof UsageRate>
export type PlanFormData = z.infer<typeof PlanFormData>
export type Discount = z.infer<typeof Discount>
