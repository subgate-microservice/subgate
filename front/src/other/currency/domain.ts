import {z} from "zod";

export const Currency = z.object({
    name: z.string(),
    symbol: z.string(),
    code: z.string(),
})

export type Currency = z.infer<typeof Currency>
