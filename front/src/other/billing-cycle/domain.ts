import {z} from "zod";

export const Period = z.enum([
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
    "Semiannual",
    "Annual",
    "Lifetime",
])


export function getNextBillingDate(_startDate: Date, _cycle: Period) {
    throw Error("NotImpl")
}


export type Period = z.infer<typeof Period>
