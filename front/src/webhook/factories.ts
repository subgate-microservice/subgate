import {WebhookCU} from "./domain.ts";
import {v4} from "uuid";

export function blankWebhookCU(): WebhookCU {
    return {
        id: v4(),
        targetUrl: "",
        eventCode: "",
    }
}