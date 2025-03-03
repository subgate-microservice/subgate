import {z} from "zod";

export const authUserValidator = z.object({
    id: z.string(),
    email: z.string(),
}).strict()

export const emailUpdateValidator = z.object({
    email: z.string(),
    password: z.string(),
}).strict()

export const passwordUpdateValidator = z.object({
    oldPassword: z.string(),
    newPassword: z.string(),
    repeatPassword: z.string(),
}).strict()

