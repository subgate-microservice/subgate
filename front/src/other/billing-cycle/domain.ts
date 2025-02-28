import {z} from "zod";
import {Select} from "../../core.ts";

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

export function getAllPeriods(): Period[] {
    return [
        Period.enum.Daily,
        Period.enum.Weekly,
        Period.enum.Monthly,
        Period.enum.Quarterly,
        Period.enum.Semiannual,
        Period.enum.Annual,
        Period.enum.Lifetime
    ]
}

export function convertPeriodIntoSelectItem(period: Period): Select<Period> {
    return {code: period, value: period}
}


export type Period = z.infer<typeof Period>
