export function findAndReplace<T>(item: T, array: T[], key: (x: T) => any, preventLookupError?: boolean) {
    if (!key) {
        key = (x) => x
    }
    for (let i = 0; i < array.length; i++) {
        if (key(array[i]) === key(item)) {
            array[i] = item
            return
        }
    }
    if (!preventLookupError) {
        throw Error("LookupError")
    }
}

export function findAndDelete<T>(item: T, array: T[], key: (x: T) => any) {
    let i = 0
    for (; i < array.length; i++) {
        if (key(array[i]) === key(item)) {
            array.splice(i, 1)
            return
        }
    }
    throw Error("LookupError")
}

export function convertArrayIntoHashMap<T>(arr: T[], key: (x: T) => string): { [index: string]: T } {
    const result: { [index: string]: T } = {}
    for (let item of arr) {
        result[key(item)] = item
    }
    return result
}

export function convertArrayIntoMapObject<T>(arr: T[], key: (x: T) => any): Map<any, T> {
    const result = new Map()
    for (let item of arr) {
        const k = key(item)
        result.set(k, item)
    }
    return result
}
