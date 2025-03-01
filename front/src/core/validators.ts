import {z} from "zod";
import {Period} from "./domain.ts";


export const discountValidator = z.object({
    title: z.string(),
    code: z.string(),
    description: z.string().optional().nullable(),
    size: z.string(),
    validUntil: z.coerce.date(),
}).strict()


export const usageRateValidator = z.object({
    title: z.string(),
    code: z.string(),
    unit: z.string(),
    availableUnits: z.number(),
    renewCycle: Period,
}).strict()

export const planValidator = z.object({
    id: z.string(),
    title: z.string(),
    price: z.number(),
    currency: z.string(),
    billingCycle: Period,
    description: z.string().optional().nullable(),
    level: z.number(),
    features: z.string().optional().nullable(),
    usageRates: usageRateValidator.array(),
    fields: z.any(),
    discounts: discountValidator.array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()