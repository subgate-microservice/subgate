import {BillingCycle, BillingCycleCode} from "./domain.ts";

const ALL_DATA: BillingCycle[] = [
    {title: "Daily", code: BillingCycleCode.enum.Daily, cycleInDays: 1},
    {title: "Monthly", code: BillingCycleCode.enum.Monthly, cycleInDays: 31},
    {title: "Quarterly", code: BillingCycleCode.enum.Quarterly, cycleInDays: 91},
    {title: "Semiannual", code: BillingCycleCode.enum.Semiannual, cycleInDays: 183},
    {title: "Annual", code: BillingCycleCode.enum.Annual, cycleInDays: 365},
]

export function getAllBillingCycles(): BillingCycle[] {
    return ALL_DATA
}

export function getBillingCycleByCode(code: BillingCycleCode): BillingCycle {
    switch (code) {
        case BillingCycleCode.enum.Daily:
            return ALL_DATA[0]
        case BillingCycleCode.enum.Monthly:
            return ALL_DATA[1]
        case BillingCycleCode.enum.Quarterly:
            return ALL_DATA[2]
        case BillingCycleCode.enum.Semiannual:
            return ALL_DATA[3]
        case BillingCycleCode.enum.Annual:
            return ALL_DATA[4]
        default:
            throw Error(`switch error (${code})`)
    }
}