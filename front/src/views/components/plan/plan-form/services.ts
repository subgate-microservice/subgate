import {Discount, PlanFormData, UsageRate} from "../../../../plan";
import {fromError} from "zod-validation-error";
import {ZodError} from "zod";
import {BillingCycle} from "../../../../other/billing-cycle";
import {Currency} from "../../../../other/currency";
import {safeArrayParsing} from "../../../../utils/other.ts";


export interface PlanFormDataValidationResult {
    title: string[],
    description: string[],
    usageRates: Record<string, string[]>,
    discounts: Record<string, string[]>,
    features: string[],
    price: string[],
    level: string[],
    billingCycle: string[],
    currency: string[],
    fields: string[],
    validated: boolean,
}

export interface InputSchema {
    title: string,
    price: number,
    currency: Currency,
    billingCycle: BillingCycle,
    description: string,
    level: number,
    features: string,
    usageRates: UsageRate[],
    discounts: Discount[],
    fields: string,
}


export function blankPlanFormDataValidationResult(): PlanFormDataValidationResult {
    return {
        title: [],
        description: [],
        usageRates: {},
        discounts: {},
        features: [],
        price: [],
        level: [],
        billingCycle: [],
        currency: [],
        fields: [],
        validated: true,
    }
}

export function validatePlanFormData(data: InputSchema): PlanFormDataValidationResult {
    const result: PlanFormDataValidationResult = {
        title: [],
        description: [],
        usageRates: {},
        discounts: {},
        features: [],
        price: [],
        level: [],
        billingCycle: [],
        currency: [],
        fields: [],
        validated: true,
    }

    if (data.fields) {
        try {
            JSON.parse(data.fields)
        } catch (err) {
            result.fields.push("Fields should be a correct json")
            result.validated = false
        }
    }

    try {
        PlanFormData.parse(convertInputSchemaToPlanFormData(data))
    } catch (err) {
        if (err instanceof ZodError) {
            err.errors.forEach((issue) => {
                const fieldName = issue.path[0] as keyof PlanFormDataValidationResult;
                if (
                    fieldName !== "usageRates"
                    && fieldName !== "discounts"
                    && fieldName !== "validated"
                    && fieldName != "fields"
                    && fieldName in result
                ) {
                    result[fieldName].push(fieldName + ": " + issue.message);
                    result.validated = false
                }
            });
        }
    }

    for (let usageRate of data.usageRates) {
        try {
            UsageRate.parse(usageRate)
        } catch (err) {
            const usageValidationError = fromError(err);
            result.usageRates[usageRate.resource] = usageValidationError.toString()
                .split("Validation error: ")[1]
                .split(";")
            result.validated = false
        }
    }

    for (let discount of data.discounts) {
        try {
            Discount.parse(discount)
        } catch (err) {
            const discountValidationError = fromError(err)
            result.discounts[discount.id] = discountValidationError.toString()
                .split("Validation error: ")[1]
                .split(";")
            result.validated = false
        }
    }
    return result
}


export function convertPlanFormDataToInputSchema(data: PlanFormData): InputSchema {
    const discounts: Discount[] = safeArrayParsing(Discount, JSON.parse(JSON.stringify(data.discounts)))
    discounts.forEach(x => x.size = x.size * 100)
    return {
        title: data.title,
        price: data.price,
        currency: data.currency,
        billingCycle: data.billingCycle,
        description: data.description,
        level: data.level,
        features: data.features,
        usageRates: JSON.parse(JSON.stringify(data.usageRates)),
        discounts,
        fields: JSON.stringify(data.fields),
    }
}

export function convertInputSchemaToPlanFormData(schema: InputSchema): PlanFormData {
    const discounts: Discount[] = safeArrayParsing(Discount,JSON.parse(JSON.stringify(schema.discounts)))
    discounts.forEach(x => x.size = x.size / 100)
    return {
        title: schema.title,
        price: schema.price,
        currency: schema.currency,
        billingCycle: schema.billingCycle,
        description: schema.description,
        level: schema.level,
        features: schema.features,
        usageRates: JSON.parse(JSON.stringify(schema.usageRates)),
        discounts,
        fields: schema.fields ? JSON.parse(schema.fields) : {},
    }
}