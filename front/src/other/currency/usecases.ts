import {Currency} from "./domain.ts";

const ALL_DATA: Currency[] = [
    {name: "RUB", code: "RUB", symbol: "₽"},
    {name: "USD", code: "USD", symbol: "$"},
]

export function getAllCurrencies(): Currency[] {
    return ALL_DATA
}

export function getCurrencyByCode(code: string): Currency {
    for (let item of ALL_DATA) {
        if (item.code === code) {
            return item
        }
    }
    throw Error(`LookupError: ${code}`)
}


export function getAmountString(currency: Currency, amount: number): string {
    const symbol = currency.symbol
    return amount >= 0 ? `${symbol}${amount}` : `-${symbol}${-amount}`
}