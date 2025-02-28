import {Webhook, WebhookFormData, WebhookSby} from "./domain.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {authRequest} from "../auth/auth-request.ts";
import {safeArrayParsing, safeParsing} from "../utils/other.ts";

class WebhookGateway{
    async createOne(item: WebhookFormData): Promise<Webhook> {
        const url = `/webhook`
        const response = (await authRequest(axiosInstance.post, url, item)).data
        return safeParsing(Webhook, response)
    }

    async getOneById(itemId: string): Promise<Webhook> {
        const url = `/webhook/${itemId}`
        const response = (await authRequest(axiosInstance.get, url)).data
        return safeParsing(Webhook, response)
    }

    async getSelected(sby: WebhookSby): Promise<Webhook[]> {
        const url = `/webhook`
        const config = {params: sby}
        const response = (await authRequest(axiosInstance.get, url, config)).data
        return safeArrayParsing(Webhook, response)
    }

    async updateOne(item: Webhook) : Promise<void> {
        const url = `/webhook/${item.id}`
        await authRequest(axiosInstance.put, url, item)
    }

    async deleteOneById(itemId: string): Promise<void> {
        const url = `/webhook/${itemId}`
        await authRequest(axiosInstance.delete, url)
    }

    async deleteSelected(sby: WebhookSby): Promise<void> {
        const url = `/webhook`
        const params = {data: sby}
        await authRequest(axiosInstance.delete, url, params)
    }
 }

export function getWebhookGateway(){
    return new WebhookGateway()
}