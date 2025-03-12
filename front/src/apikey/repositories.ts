import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {safeArrayParsing, safeParsing, toCamelCase, toSnakeCase} from "../shared/services/other.ts";
import {Apikey, ApikeyCU} from "./domain.ts";
import {apikeyValidator} from "./validators.ts";

export class ApikeyRepo {
    async getAll(): Promise<Apikey[]> {
        const url = `/apikey`
        const response = (await authRequest(axiosInstance.get, url))
        console.log(response.data)
        return safeArrayParsing(apikeyValidator, toCamelCase(response.data))
    }

    async createOne(data: ApikeyCU): Promise<[Apikey, string]> {
        const url = `/apikey`
        const payload = toSnakeCase(data)
        const response = await authRequest(axiosInstance.post, url, payload)
        return [safeParsing(apikeyValidator, toCamelCase(response.data[0])), response.data[1]]
    }

    async deleteOneById(id: string): Promise<void> {
        const url = `/apikey/${id}`
        await authRequest(axiosInstance.delete, url)
    }
}
