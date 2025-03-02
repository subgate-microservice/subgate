import {z} from "zod";

export const webhookValidator = z.object({
    id: z.string(),
    eventCode: z.string(),
    targetUrl: z.string(),
    delays: z.number().array(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
})
