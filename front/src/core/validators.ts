import {z} from "zod";


export const periodValidator = z.enum([
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "semiannual",
    "annual",
    "lifetime",
])


export const discountValidator = z.object({
    title: z.string().min(2, "Title must contain at least 2 symbols"),
    code: z.string().min(2, "Code must contain at least 2 symbols"),
    description: z.string().optional().nullable(),
    size: z.number(),
    validUntil: z.coerce.date(),
}).strict()


export const usageRateValidator = z.object({
    title: z.string().min(2, "Title must contain at least 2 symbols"),
    code: z.string().min(2, "Code must contain at least 2 symbols"),
    unit: z.string().min(2, "Unit must contain at least 2 symbols"),
    availableUnits: z.number().positive("Available units must be positive"),
    renewCycle: periodValidator,
}).strict()

export const usageValidator = z.object({
    title: z.string().min(2),
    code: z.string().min(2),
    unit: z.string().min(2),
    availableUnits: z.number().positive(),
    renewCycle: periodValidator,
    lastRenew: z.coerce.date(),
    usedUnits: z.number(),
}).strict()

export const planValidator = z.object({
    id: z.string(),
    title: z.string().min(2),
    price: z.number().min(0),
    currency: z.string().min(2),
    billingCycle: periodValidator,
    description: z.string().optional().nullable(),
    level: z.number().positive().int(),
    features: z.string().optional().nullable(),
    usageRates: usageRateValidator.array(),
    fields: z.any(),
    discounts: discountValidator.array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()


export const planCUValidator = z.object({
    id: z.string(),
    title: z.string().min(2),
    price: z.number().min(0),
    currency: z.string(),
    billingCycle: periodValidator,
    description: z.string().nullable(),
    usageRates: usageRateValidator.array(),
    discounts: discountValidator.array(),
    level: z.number().positive(),
    features: z.string().nullable(),
    fields: z.any(),
}).strict()

const planInfoValidator = z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    level: z.number(),
    features: z.string().optional().nullable(),
}).strict()

const billingInfoValidator = z.object({
    price: z.number(),
    currency: z.string(),
    billingCycle: periodValidator,
    lastBilling: z.coerce.date(),
    savedDays: z.number(),
}).strict()

const subscriptionStatusValidator = z.enum(["active", "paused", "expired"])

export const subscriptionValidator = z.object({
    id: z.string(),
    subscriberId: z.string(),
    planInfo: planInfoValidator,
    billingInfo: billingInfoValidator,
    status: subscriptionStatusValidator,
    pausedFrom: z.coerce.date().nullable().optional(),
    autorenew: z.boolean(),
    usages: usageValidator.array(),
    discounts: discountValidator.array(),
    fields: z.any(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()

export const subscriptionCUValidator = z.object({
    id: z.string(),
    subscriberId: z.string().min(1),
    planInfo: planInfoValidator,
    billingInfo: billingInfoValidator,
    status: subscriptionStatusValidator,
    pausedFrom: z.coerce.date().nullable().optional(),
    autorenew: z.boolean(),
    usages: usageRateValidator.array(),
    discounts: discountValidator.array(),
    fields: z.any(),
}).strict()