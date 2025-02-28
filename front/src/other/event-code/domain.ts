import {z} from "zod";

export const EventCode = z.enum([
    "SubscriptionCreated",
    "SubscriptionUpdated",
    "SubscriptionExpired",
    "SubscriptionDeleted",
    "PlanCreated",
    "PlanUpdated",
    "PlanDeleted",
    "WebhookCreated",
    "WebhookUpdated",
    "WebhookDeleted",
])

export type EventCode = z.infer<typeof EventCode>