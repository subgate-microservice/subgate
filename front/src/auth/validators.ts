import {z} from "zod";

export const authUserValidator = z.object({
    id: z.string(),
}).strict()

export const emailUpdateValidator = z.object({
    email: z.string().email({ message: "Invalid email format" }),
    password: z.string(),
}).strict()

export const passwordUpdateValidator = z.object({
    oldPassword: z.string(),
    newPassword: z.string().min(6),
    repeatPassword: z.string(),
})
    .strict()
    .refine((data) => data.newPassword === data.repeatPassword, {
        message: "Passwords do not match",
        path: ["repeatPassword"], // Ошибка будет привязана к этому полю
    })
    .innerType()

