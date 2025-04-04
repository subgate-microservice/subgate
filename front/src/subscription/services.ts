import {Period, Subscription} from "./domain.ts";

export function getCycleInDays(period: Period) {
    const mapper = {
        [Period.Daily]: 1,
        [Period.Weekly]: 7,
        [Period.Monthly]: 30,
        [Period.Quarterly]: 92,
        [Period.Semiannual]: 183,
        [Period.Annual]: 365,
        [Period.Lifetime]: 365_000,
    }
    return mapper[period]
}

export function getNextBilling(target: Subscription): Date {
    const result = new Date(target.billingInfo.lastBilling)
    const days = getCycleInDays(target.billingInfo.billingCycle) + target.billingInfo.savedDays
    result.setDate(result.getDate() + days)
    return result
}

export function getAmountString(currency: string, amount: number): string {
    return `${amount} ${currency}`
}