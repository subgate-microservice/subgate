import {z, ZodError} from "zod";
import {Discount, Period, PlanCreate} from "./domain.ts";
import {fromError} from "zod-validation-error";

export interface DiscountsValidationResult {
    [index: string]: string[]
}

export interface PlanCreateValidationResult {
    title: string[]
    description: string[]
    discounts: DiscountsValidationResult
    features: string[]
    price: string[]
    level: string[]
    billingCycle: string[]
    currency: string[]
    fields: string[]
    validated: boolean
}

export function PlanCreateErrors(): PlanCreateValidationResult {
    return {
        title: [],
        description: [],
        discounts: {},
        features: [],
        price: [],
        level: [],
        billingCycle: [],
        currency: [],
        fields: [],
        validated: true
    }
}

export function validateDiscounts(discounts: Discount[]): DiscountsValidationResult {
    const validator = z.object({
        title: z.string().min(2),
        code: z.string().min(2),
        size: z.number().min(0).max(100),
        validUntil: z.date(),
        description: z.string().nullable().optional(),
    })
    const result: DiscountsValidationResult = {}
    for (let discount of discounts) {
        try {
            validator.parse(discount)
        } catch (err) {
            const discountValidationError = fromError(err)
            result[discount.code] = discountValidationError
                .toString()
                .split("Validation error: ")[1]
                .split(";")
        }
    }
    return result
}

export function validatePlanCreate(planCreate: PlanCreate): PlanCreateValidationResult {
    const simpleValidator = z.object({
        title: z.string(),
        price: z.number(),
        currency: z.string(),
        billingCycle: Period,
        description: z.string().nullable(),
        level: z.number(),
        features: z.string().nullable(),
    })
    const result: PlanCreateValidationResult = PlanCreateErrors()

    try {
        simpleValidator.parse(planCreate)
    } catch (err) {
        if (err instanceof ZodError) {
            err.errors.forEach((issue) => {
                const fieldName = issue.path[0] as keyof PlanCreateValidationResult
                // @ts-ignore
                if (result[fieldName] === undefined) result[fieldName] = []
                // @ts-ignore
                result[fieldName]!.push(fieldName + ": " + issue.message);
            })
            result.validated = false
        }
    }
    const discountValidation = validateDiscounts(planCreate.discounts)
    if (!discountValidation.v) {
        result.discounts = discountValidation
        result.validated = false
    }
    return result
}
