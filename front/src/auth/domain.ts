import {z} from "zod";

export const AuthUser = z.object({
    id: z.string(),
    email: z.string(),
}).strict()

export const UpdateEmailForm = z.object({
    email: z.string(),
    password: z.string(),
}).strict()

export const UpdatePasswordForm = z.object({
    oldPassword: z.string(),
    newPassword: z.string(),
    repeatPassword: z.string(),
}).strict()


export const ApikeyFormData = z.object({
    title: z.string(),
})


export type AuthUser = z.infer<typeof AuthUser>
export type UpdateEmailForm = z.infer<typeof UpdateEmailForm>
export type UpdatePasswordForm = z.infer<typeof UpdatePasswordForm>
export type ApikeyFormData = z.infer<typeof ApikeyFormData>

