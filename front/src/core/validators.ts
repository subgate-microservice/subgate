import {z} from "zod";
import {Period} from "./domain.ts";


export const discountValidator = z.object({
    title: z.string().min(2),
    code: z.string().min(2),
    description: z.string().optional().nullable(),
    size: z.number(),
    validUntil: z.coerce.date(),
}).strict()


export const usageRateValidator = z.object({
    title: z.string().min(2),
    code: z.string().min(2),
    unit: z.string().min(2),
    availableUnits: z.number().positive(),
    renewCycle: Period,
}).strict()

export const planValidator = z.object({
    id: z.string(),
    title: z.string().min(2),
    price: z.number().positive(),
    currency: z.string().min(2),
    billingCycle: Period,
    description: z.string().optional().nullable(),
    level: z.number().positive().int(),
    features: z.string().optional().nullable(),
    usageRates: usageRateValidator.array(),
    fields: z.any(),
    discounts: discountValidator.array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()