import {
    SubscriptionFormData,
    SubscriptionStatus,
    Usage
} from "../../../../subscription/domain.ts";
import {v4, validate} from "uuid";
import {fromError} from "zod-validation-error";
import {Discount, getSelectedPlans, Plan} from "../../../../plan";
import {Period} from "../../../../other/billing-cycle";

export interface SelectionItem<T> {
    title: string,
    code: string,
    value: T
}

export interface UsageInputSchema {
    resource: string,
    unit: string,
    availableUnits: number,
    usedUnits: number,
    renewCycle: SelectionItem<Period>,
}

export interface InputSchema {
    subscriberId: string,
    selectedBillingCycle: SelectionItem<Period> | null,
    selectedPlan: SelectionItem<Plan> | null,
    selectedStatus: SelectionItem<SubscriptionStatus>,
    discounts: Discount[],
    usages: UsageInputSchema[],
    lastBilling: Date,
    pausedFrom: Date | null,
    autorenew: boolean,
}

export interface ValidationResult {
    subscriberId: string[],
    planId: string[],
    status: string[],
    trialPeriod: string[],
    discounts: Record<string, string[]>,
    usages: Record<string, string[]>,
    startDate: string[],
    autoRenew: string[],
    validated: boolean,
}

export function blankValidationResult(): ValidationResult {
    return {
        subscriberId: [],
        planId: [],
        status: [],
        trialPeriod: [],
        discounts: {},
        usages: {},
        startDate: [],
        autoRenew: [],
        validated: true,
    }
}

export function validateInputSchema(data: InputSchema): ValidationResult {
    const result: ValidationResult = blankValidationResult()

    if (data.subscriberId.length === 0) {
        result.subscriberId.push("Subscriber ID should have at least 1 character")
        result.validated = false
    }

    if (!data.selectedPlan) {
        result.planId.push("You should select a plan")
        result.validated = false
    }

    if (!validate(data.selectedPlan!.value.id)) {
        result.planId.push("Plan ID should be a uuid4 string")
        result.validated = false
    } else {
        for (let usage of data.usages) {
            try {
                Usage.parse(convertSchemaToUsages(usage))
            } catch (err) {
                const usageValidationError = fromError(err);
                result.usages[usage.resource] = usageValidationError.toString()
                    .split("Validation error: ")[1]
                    .split(";")
                result.validated = false
            }
        }
    }

    for (let discount of data.discounts) {
        try {
            Discount.parse(discount)
        } catch (err) {
            const discountValidationError = fromError(err)
            result.discounts[discount.code] = discountValidationError.toString()
                .split("Validation error: ")[1]
                .split(";")
            result.validated = false
        }
    }

    return result
}

export function blankInputSchema(): InputSchema {
    return {
        subscriberId: v4(),
        selectedBillingCycle: null,
        selectedPlan: null,
        selectedStatus: {
            title: SubscriptionStatus.enum.Active,
            code: SubscriptionStatus.enum.Active,
            value: SubscriptionStatus.enum.Active
        },
        discounts: [],
        usages: [],
        lastBilling: new Date(),
        pausedFrom: null,
        autorenew: false,
    }
}

function convertUsageToSchema(data: Usage): UsageInputSchema {
    return {
        resource: data.resource,
        unit: data.unit,
        availableUnits: data.availableUnits,
        usedUnits: data.usedUnits,
        renewCycle: {title: data.renewCycle, code: data.renewCycle, value: data.renewCycle},
    }
}

function convertSchemaToUsages(schema: UsageInputSchema): Usage {
    return {
        resource: schema.resource,
        unit: schema.unit,
        availableUnits: schema.availableUnits,
        usedUnits: schema.usedUnits,
        renewCycle: schema.renewCycle.value,
    }
}

export function convertFormDataToInputSchema(data: SubscriptionFormData): InputSchema {
    return {
        subscriberId: data.subscriberId,
        selectedBillingCycle: {
            title: data.plan.billingCycle,
            code: data.plan.billingCycle, value:
            data.plan.billingCycle,
        },
        selectedPlan: {
            title: data.plan.title,
            code: data.plan.id,
            value: data.plan,
        },
        selectedStatus: {
            title: data.status,
            code: data.status,
            value: data.status,
        },
        discounts: data.plan.discounts,
        usages: data.usages.map(item => convertUsageToSchema(item)),
        lastBilling: data.lastBilling,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew,
    }
}

export function convertInputSchemaToFormData(schema: InputSchema): SubscriptionFormData {
    const plan = {...schema.selectedPlan!.value}
    plan.billingCycle = schema.selectedBillingCycle!.value
    plan.discounts = schema.discounts
    return {
        lastBilling: schema.lastBilling,
        createdAt: schema.lastBilling,
        updatedAt: schema.lastBilling,
        subscriberId: schema.subscriberId,
        plan: plan,
        status: schema.selectedStatus.value,
        usages: schema.usages.map(item => convertSchemaToUsages(item)),
        pausedFrom: schema.pausedFrom,
        autorenew: schema.autorenew
    }
}

export async function getAllPlans(): Promise<SelectionItem<Plan>[]> {
    let plans = await getSelectedPlans({})
    return plans.map(item => ({title: item.title, code: item.id, value: item}))
}

export function addCustomPlanOrReplaceIfTheOneAlreadyExist(allPlans: SelectionItem<Plan>[], customPlan: Plan): void {
    const hash = customPlan.id
    for (let i = 0; i < allPlans.length; i++) {
        const plan = allPlans[i]
        if (hash === plan.value.id) {
            allPlans[i] = {title: customPlan.title, code: customPlan.id, value: customPlan}
            return
        }
    }
    allPlans.push({title: customPlan.title, code: customPlan.id, value: customPlan})
}

export function getAllStatuses() {
    return [
        {
            title: SubscriptionStatus.enum.Active,
            code: SubscriptionStatus.enum.Active,
            value: SubscriptionStatus.enum.Active
        },
        {
            title: SubscriptionStatus.enum.Paused,
            code: SubscriptionStatus.enum.Paused,
            value: SubscriptionStatus.enum.Paused
        },
    ]
}

export function getAllPeriods() {
    const periods = [Period.enum.Annual]
    return periods.map(item => ({title: item, code: item, value: item}))
}


export function createUsageObject(plans: Plan[]): Record<string, UsageInputSchema[]> {
    const result: Record<string, UsageInputSchema[]> = {}
    for (let plan of plans) {
        result[plan.id] = []
        for (let usageRate of plan.usageRates) {
            result[plan.id].push(
                {
                    resource: usageRate.code,
                    availableUnits: usageRate.availableUnits,
                    unit: usageRate.unit,
                    usedUnits: 0,
                    renewCycle: {
                        title: usageRate.renewCycle,
                        code: usageRate.renewCycle,
                        value: usageRate.renewCycle
                    },
                }
            )
        }
    }

    return result
}

export function createDiscountObject(plans: Plan[]): Record<string, Discount[]> {
    const result: Record<string, Discount[]> = {}
    for (let plan of plans) {
        result[plan.id] = []
        for (let discount of plan.discounts) {
            result[plan.id].push(discount)
        }
    }
    return result
}