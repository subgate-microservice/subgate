import {Webhook, WebhookCU} from "./domain.ts";
import {safeArrayParsing, safeParsing, toCamelCase, toSnakeCase} from "../shared/services/other.ts";
import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {webhookValidator} from "./validators.ts";
import {AxiosRequestConfig} from "axios";

export interface WebhookSby {
    ids?: string[]
}

export class WebhookRepo {
    async createOne(data: WebhookCU): Promise<Webhook> {
        const url = "webhook"
        const payload = toSnakeCase(data)
        const response = await authRequest(axiosInstance.post, url, payload)
        return await this.getById(response.data)
    }

    async updateOne(data: WebhookCU): Promise<Webhook> {
        const url = `/webhook/${data.id}`
        const payload = toSnakeCase(data)
        await authRequest(axiosInstance.patch, url, payload)
        return await this.getById(data.id)
    }

    async getAll(): Promise<Webhook[]> {
        const url = "/webhook"
        const response = await authRequest(axiosInstance.get, url)
        return safeArrayParsing(webhookValidator, toCamelCase(response.data))
    }

    async getById(webhookId: string): Promise<Webhook> {
        const url = `/webhook/${webhookId}`
        const response = await authRequest(axiosInstance.get, url)
        return safeParsing(webhookValidator, toCamelCase(response.data))
    }

    async deleteById(webhookId: string): Promise<void> {
        const url = `/webhook/${webhookId}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: WebhookSby): Promise<void> {
        const url = "/webhook"

        const params = new URLSearchParams();
        if (sby.ids) sby.ids.forEach(id => params.append("ids", id))

        const config: AxiosRequestConfig = {params}
        await authRequest(axiosInstance.delete, url, config)
    }
}