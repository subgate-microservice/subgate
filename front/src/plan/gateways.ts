import {Discount, Plan, PlanFormData, PlanSby, UsageRate} from "./domain.ts";
import {authRequest} from "../auth/auth-request.ts";
import {safeArrayParsing, safeParsing} from "../utils/other.ts";
import {Id} from "../core.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {BillingCycle} from "../other/billing-cycle";
import {getCurrencyByCode} from "../other/currency";

export interface PlanSchema {
    id: string,
    title: string,
    price: number,
    currency: string,
    billingCycle: BillingCycle,
    description: string,
    level: number,
    features: string,
    usageRates: UsageRate[],
    fields: Record<string, any>,
    discounts: Discount[],
    createdAt: Date,
    updatedAt: Date,
}

export function deserializePlan(data: PlanSchema): Plan {
    return {
        id: data.id,
        title: data.title,
        price: data.price,
        currency: getCurrencyByCode(data.currency),
        billingCycle: data.billingCycle,
        description: data.description,
        level: data.level,
        features: data.features,
        usageRates: data.usageRates,
        discounts: data.discounts,
        fields: data.fields,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
    }
}

export function serializePlan(data: Plan): PlanSchema {
    return {
        id: data.id,
        title: data.title,
        price: data.price,
        currency: data.currency.code,
        billingCycle: data.billingCycle,
        description: data.description,
        level: data.level,
        features: data.features,
        usageRates: data.usageRates,
        discounts: data.discounts,
        fields: data.fields,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
    }
}


interface PlanCreateSchema {
    title: string,
    price: number,
    currency: string,
    billingCycle: BillingCycle,
    description: string,
    level: number,
    features: string,
    usageRates: UsageRate[],
    discounts: Discount[],
    fields: Record<string, any>,
}

export function serializePlanFormData(data: PlanFormData): PlanCreateSchema {
    return {
        title: data.title,
        price: data.price,
        currency: data.currency.code,
        billingCycle: data.billingCycle,
        description: data.description,
        level: data.level,
        features: data.features,
        usageRates: data.usageRates,
        discounts: data.discounts,
        fields: data.fields,
    }
}


class PlanFakeGateway {
    async getSelected(sby: PlanSby): Promise<Plan[]> {
        console.log(sby)
        throw Error("NotImpl")
    }

    async createOne(data: PlanFormData): Promise<Plan> {
        console.log(data)
        throw Error("NotImpl")

    }

    async updateOne(data: Plan): Promise<void> {
        console.log(data)
        throw Error("NotImpl")

    }

    async deleteOne(planId: Id): Promise<void> {
        console.log(planId)
        throw Error("NotImpl")
    }
}

class PlanGateway extends PlanFakeGateway {
    async getOneById(id: string): Promise<Plan> {
        const url = `/plan/${id}`
        const response: PlanSchema = (await authRequest(axiosInstance.get, url)).data
        const plan = deserializePlan(response)
        return safeParsing(Plan, plan)
    }

    async getSelected(sby: PlanSby): Promise<Plan[]> {
        const url = "/plan"
        const response: PlanSchema[] = (await authRequest(axiosInstance.get, url, {params: sby})).data
        const plans = response.map(item => deserializePlan(item))
        return safeArrayParsing(Plan, plans)
    }

    async createOne(data: PlanFormData): Promise<Plan> {
        const url = "/plan"
        const dataForSend = serializePlanFormData(data)
        console.log(dataForSend)

        const response: PlanSchema = (await authRequest(axiosInstance.post, url, dataForSend)).data
        const plan = deserializePlan(response)
        return safeParsing(Plan, plan)
    }

    async updateOne(data: Plan): Promise<void> {
        const dataForSend = serializePlan(data)
        const url = `/plan/${data.id}`
        await authRequest(axiosInstance.put, url, dataForSend)
    }

    async deleteOne(planId: Id): Promise<void> {
        const url = `/plan/${planId}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: PlanSby): Promise<void> {
        const url = `/plan`
        const params = {data: sby}
        await authRequest(axiosInstance.delete, url, params)
    }
}

export function getPlanGateway() {
    return new PlanGateway()
}