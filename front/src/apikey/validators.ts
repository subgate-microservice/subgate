import {z} from "zod";

export const apikeyValidator = z.object({
    id: z.string(),
    title: z.string(),
    createdAt: z.coerce.date(),
    updatedAt: z.coerce.date(),
}).strict()

export const apikeyCUValidator = z.object({
    title: z.string().min(2),
})