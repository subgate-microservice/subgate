import {WebhookCU} from "./domain.ts";

export function blankWebhookCU(): WebhookCU {
    return {
        targetUrl: "",
        eventCode: "",
    }
}