import {z} from "zod";

export const apikeyValidator = z.object({
    publicId: z.string(),
    title: z.string(),
    createdAt: z.coerce.date(),
}).strict()

export const apikeyCUValidator = z.object({
    title: z.string().min(2),
})