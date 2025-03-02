export interface Webhook{
    id: string
    eventCode: string
    targetUrl: string
    delays: number[]
    createdAt: Date
    updatedAt: Date
}

export interface WebhookCU {
    id: string
    eventCode: string
    targetUrl: string
    delays: number[]
}