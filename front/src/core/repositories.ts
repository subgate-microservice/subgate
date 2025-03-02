import {Plan, PlanCreate, PlanUpdate, Subscription, SubscriptionUpdate} from "./domain.ts";
import {safeArrayParsing, safeParsing, toCamelCase, toSnakeCase} from "../utils/other.ts";
import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {planValidator, subscriptionValidator} from "./validators.ts";
import {AxiosRequestConfig} from "axios";

export interface PlanSby {
    ids?: string[],
}

export class PlanRepo {
    async create(item: PlanCreate): Promise<Plan> {
        const url = "/plan"
        const data = toSnakeCase(item)
        const response = await authRequest(axiosInstance.post, url, data)
        return await this.getById(response.data)
    }

    async update(item: PlanUpdate): Promise<Plan> {
        const url = `/plan/${item.id}`
        const data = toSnakeCase(item)
        await authRequest(axiosInstance.put, url, data)
        return await this.getById(item.id)
    }

    async getAll(): Promise<Plan[]> {
        const url = "plan"
        const response = await authRequest(axiosInstance.get, url)
        return safeArrayParsing(planValidator, toCamelCase(response.data))
    }

    async getById(planId: string): Promise<Plan> {
        const url = `/plan/${planId}`
        const response = await authRequest(axiosInstance.get, url)
        return safeParsing(planValidator, toCamelCase(response.data))
    }

    async deleteById(planId: string): Promise<void> {
        const url = `/plan/${planId}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: PlanSby): Promise<void> {
        const url = `/plan`
        const params = {data: sby}
        await authRequest(axiosInstance.delete, url, params)
    }
}


export interface SubscriptionSby {
    ids?: string[]
}

export class SubscriptionRepo {
    async create(item: SubscriptionUpdate): Promise<Subscription> {
        const url = "/subscription"
        const data = toSnakeCase(item)
        const response = await authRequest(axiosInstance.post, url, data)
        return await this.getById(response.data)

    }

    async update(item: SubscriptionUpdate): Promise<Subscription> {
        const url = `/subscription/${item.id}`
        const data = toSnakeCase(item)
        await authRequest(axiosInstance.put, url, data)
        return await this.getById(item.id)
    }

    async getById(subId: string): Promise<Subscription> {
        const url = `/subscription/${subId}`
        const response = await authRequest(axiosInstance.get, url)
        return safeParsing(subscriptionValidator, toCamelCase(response.data))
    }

    async getSelected(_sby?: SubscriptionSby): Promise<Subscription[]> {
        const url = "/subscription"
        const response = await authRequest(axiosInstance.get, url)
        return safeArrayParsing(subscriptionValidator, toCamelCase(response.data))
    }

    async deleteById(subId: string): Promise<void> {
        const url = `/subscription/${subId}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: SubscriptionSby): Promise<void> {
        const url = "/subscription"

        const params = new URLSearchParams();
        if (sby.ids) sby.ids.forEach(id => params.append("ids", id))

        const config: AxiosRequestConfig = {params}
        await authRequest(axiosInstance.delete, url, config)
    }
}