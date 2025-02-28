import {AxiosResponse} from "axios";
import {fiefAuth, fiefLogout} from "./fief.ts";

export function getAuthHeaders() {
    // const tokenInfo = {access_token: "FakeAuthToken"}
    const tokenInfo = fiefAuth.getTokenInfo();

    if (tokenInfo) {
        return {
            "Authorization": `Bearer ${tokenInfo.access_token}`,
        }
    }
    return {}
}

export async function authRequest(f: (...x: any[]) => Promise<AxiosResponse>, ...args: any[]): Promise<AxiosResponse> {
    try {
        return await f(...args)
    } catch (err: any) {
        console.error("Auth request failed")
        if (!err?.response?.ok) {
            if (err.response.status === 401 || err.response.status === 403) {
                await fiefLogout()
                throw Error("AuthError")
            }
        }
        throw err
    }
}

export async function maybeAuthRequest(f: (...x: any[]) => Promise<AxiosResponse>, ...args: any[]): Promise<AxiosResponse> {
    return authRequest(f, ...args)
}
