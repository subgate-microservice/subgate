import {AxiosResponse} from "axios";

export async function authRequest(f: (...x: any[]) => Promise<AxiosResponse>, ...args: any[]): Promise<AxiosResponse> {
    try {
        return await f(...args)
    } catch (err: any) {
        console.error("Auth request failed")
        if (!err?.response?.ok) {
            if (err.response.status === 401 || err.response.status === 403) {
                throw Error("AuthError")
            }
        }
        throw err
    }
}
