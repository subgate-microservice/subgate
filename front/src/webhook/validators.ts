import {z} from "zod";
import {EVENT_CODES} from "./enums.ts";

const eventCodeValidator = z.enum(EVENT_CODES, {
    message: "Invalid EventCode"
})

export const webhookValidator = z.object({
    id: z.string(),
    eventCode: z.string(),
    targetUrl: z.string().url(),
    delays: z.number().min(0).array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()

export const webhookCUValidator = z.object({
    id: z.string(),
    eventCode: eventCodeValidator,
    targetUrl: z.string().url(),
}).strict()
