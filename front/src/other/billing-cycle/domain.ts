import {z} from "zod";

export const BillingCycleCode = z.enum([
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
    "Semiannual",
    "Annual",
])

export const BillingCycle = z.object({
    title: z.string(),
    code: z.string(),
    cycleInDays: z.number(),
})

export function getNextBillingDate(startDate: Date, cycle: BillingCycle) {
    const newDate = new Date(startDate);
    newDate.setDate(newDate.getDate() + cycle.cycleInDays);
    return newDate;
}


export type BillingCycle = z.infer<typeof BillingCycle>
export type BillingCycleCode = z.infer<typeof BillingCycleCode>
