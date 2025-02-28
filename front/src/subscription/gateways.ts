import {
    SubscriptionSby,
    Subscription,
    SubscriptionStatus,
    SubscriptionFormData,
    Usage,
} from "./domain.ts";
import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {safeArrayParsing, safeParsing} from "../utils/other.ts";
import {deserializePlan, PlanSchema, serializePlan} from "../plan/gateways.ts";


interface SubscriptionSchema {
    id: string,
    subscriberId: string,
    plan: PlanSchema,
    status: SubscriptionStatus,
    usages: Usage[],
    createdAt: Date,
    updatedAt: Date,
    lastBilling: Date,
    pausedFrom: Date | null,
    autorenew: boolean,
}

interface SubscriptionFormSchema {
    subscriberId: string,
    plan: PlanSchema,
    status: SubscriptionStatus,
    createdAt: Date,
    updatedAt: Date,
    lastBilling: Date,
    pausedFrom: Date | null,
    autorenew: boolean,
    usages: Usage[],
}

function deserializeSubscription(data: SubscriptionSchema): Subscription {
    return {
        id: data.id,
        lastBilling: data.lastBilling,
        subscriberId: data.subscriberId,
        plan: deserializePlan(data.plan),
        status: data.status,
        usages: data.usages,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew
    }
}

export function serializeSubscription(data: Subscription): SubscriptionSchema {
    return {
        id: data.id,
        lastBilling: data.lastBilling,
        subscriberId: data.subscriberId,
        plan: serializePlan(data.plan),
        status: data.status,
        usages: data.usages,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew,
    }
}

export function deserializeSubscriptionForm(data: SubscriptionFormData): SubscriptionFormSchema {
    return {
        subscriberId: data.subscriberId,
        plan: serializePlan(data.plan),
        status: data.status,
        usages: data.usages,
        lastBilling: data.lastBilling,
        pausedFrom: data.pausedFrom,
        autorenew: data.autorenew,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
    }
}

class SubscriptionGateway {
    async getSelected(sby: SubscriptionSby): Promise<Subscription[]> {
        const url = `/subscription`
        const response: SubscriptionSchema[] = (await authRequest(axiosInstance.get, url, sby)).data
        const data = response.map(item => deserializeSubscription(item))
        return safeArrayParsing(Subscription, data)
    }

    async getOne(subId: string): Promise<Subscription> {
        const url = `/subscription/${subId}`
        const response: SubscriptionSchema = (await authRequest(axiosInstance.get, url)).data
        const sub = deserializeSubscription(response)
        return safeParsing(Subscription, sub)
    }

    async createOne(data: SubscriptionFormData): Promise<Subscription> {
        const url = `/subscription`
        const dataForSend = deserializeSubscriptionForm(data)
        const response: SubscriptionSchema = (await authRequest(axiosInstance.post, url, dataForSend)).data
        const sub = deserializeSubscription(response)
        return safeParsing(Subscription, sub)
    }

    async updateOne(data: Subscription): Promise<void> {
        const url = `/subscription/${data.id}`
        const dataForSend = serializeSubscription(data)
        await authRequest(axiosInstance.put, url, dataForSend)
    }

    async deleteOne(id: string): Promise<void> {
        const url = `/subscription/${id}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: SubscriptionSby): Promise<void> {
        const url = `/subscription`
        const params = {data: sby}
        await authRequest(axiosInstance.delete, url, params)
    }
}

export function getSubscriptionGateway(): SubscriptionGateway {
    return new SubscriptionGateway()
}