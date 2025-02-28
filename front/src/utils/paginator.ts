export interface Paginated {
    skip: number,
    limit: number,
}

export class Paginator<T> {
    private readonly sbyForNext: Paginated
    private readonly callback: (x: Paginated) => Promise<T[]>
    private stopNextLoading = false

    constructor(sby: Paginated, callback: (x: Paginated) => Promise<T[]>) {
        this.sbyForNext = {...sby}
        this.callback = callback
    }

    async next(): Promise<T[]> {
        if (this.stopNextLoading) return []
        const data = await this.callback(this.sbyForNext)
        this.sbyForNext.skip += this.sbyForNext.limit
        if (data.length < this.sbyForNext.limit) this.stopNextLoading = true
        return data
    }

    async max(): Promise<T[]> {
        if (this.stopNextLoading) return []
        this.sbyForNext.limit = 99_999
        console.log("loading max: ", this.sbyForNext)
        const data = await this.callback(this.sbyForNext)
        this.stopNextLoading = true
        return data
    }
}