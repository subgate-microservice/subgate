import {z} from "zod";
import {EventCode} from "../other/event-code";



export const Webhook = z.object({
    id: z.string(),
    eventCode: EventCode,
    targetUrl: z.string(),
    createdAt: z.coerce.date(),
})


export const WebhookFormData = z.object({
    eventCode: EventCode,
    targetUrl: z.string(),
})

export function convertFormDataToWebhook(data: WebhookFormData, id: string, createdAt: Date): Webhook {
    return {
        id,
        createdAt,
        eventCode: data.eventCode,
        targetUrl: data.targetUrl,
    }
}

export function convertWebhookToFormData(data: Webhook): WebhookFormData{
    return {
        eventCode: data.eventCode,
        targetUrl: data.targetUrl,
    }
}

export interface WebhookSby {

}

export type Webhook = z.infer<typeof Webhook>
export type WebhookFormData = z.infer<typeof WebhookFormData>
