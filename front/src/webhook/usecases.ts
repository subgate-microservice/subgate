import {getWebhookGateway} from "./gateways.ts";
import {Webhook, WebhookFormData, WebhookSby} from "./domain.ts";

export async function getWebhookById(id: string): Promise<Webhook> {
    return await getWebhookGateway().getOneById(id)
}

export async function getSelectedWebhooks(sby: WebhookSby): Promise<Webhook[]> {
    return await getWebhookGateway().getSelected(sby)
}

export async function createWebhook(data: WebhookFormData): Promise<Webhook> {
    return getWebhookGateway().createOne(data)
}

export async function updateWebhook(data: Webhook): Promise<void> {
    await getWebhookGateway().updateOne(data)
}

export async function deleteWebhookById(id: string): Promise<void> {
    await getWebhookGateway().deleteOneById(id)
}

export async function deleteSelectedWebhooks(sby: WebhookSby): Promise<void> {
    await getWebhookGateway().deleteSelected(sby)
}