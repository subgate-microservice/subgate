import {z} from "zod";
import {Plan} from "../plan";
import {recursive} from "../utils/other.ts";
import {BillingCycle} from "../other/billing-cycle";


export const SubscriptionStatus = z.enum(["Active", "Paused"])


export const Usage = z.object({
    resource: z.string().min(3),
    unit: z.string().min(1),
    availableUnits: z.number().gte(0),
    usedUnits: z.number().gte(0),
    renewCycle: BillingCycle,
}).strict()

export const Subscription = z.object({
    id: z.string(),
    plan: Plan,
    subscriberId: z.string(),
    status: SubscriptionStatus,
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
    lastBilling: z.coerce.date(),
    pausedFrom: z.coerce.date().nullable(),
    autorenew: z.boolean(),
    usages: Usage.array(),
}).strict()


export const SubscriptionFormData = z.object({
    subscriberId: z.string(),
    plan: Plan,
    status: SubscriptionStatus,
    lastBilling: z.date(),
    pausedFrom: z.date().nullable(),
    autorenew: z.boolean(),
    usages: Usage.array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()

export interface SubscriptionSby {

}

export function convertFormDataToSubscription(
    data: SubscriptionFormData,
    subId: string,
): Subscription {
    data = recursive(data)
    return {
        id: subId,
        subscriberId: data.subscriberId,
        plan: data.plan,
        status: data.status,
        usages: data.usages,
        lastBilling: data.lastBilling,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
    }
}

export function convertSubscriptionToFormData(data: Subscription): SubscriptionFormData {
    data = recursive(data)
    return {
        subscriberId: data.subscriberId,
        plan: data.plan,
        status: data.status,
        usages: data.usages,
        lastBilling: data.lastBilling,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
    }
}

export type SubscriptionStatus = z.infer<typeof SubscriptionStatus>
export type Usage = z.infer<typeof Usage>
export type Subscription = z.infer<typeof Subscription>
export type SubscriptionFormData = z.infer<typeof SubscriptionFormData>



