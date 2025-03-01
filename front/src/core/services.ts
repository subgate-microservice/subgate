import {Plan, PlanCreate} from "./domain.ts";
import {safeArrayParsing, safeParsing, toCamelCase, toSnakeCase} from "../utils/other.ts";
import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {planValidator} from "./validators.ts";

export class PlanService {
    async create(item: PlanCreate): Promise<Plan> {
        const url = "/plan"
        const data = toSnakeCase(item)
        const cResponse = await authRequest(axiosInstance.post, url, data)
        const rResponse = await authRequest(axiosInstance.get, `/plan/${cResponse.data}`)
        return safeParsing(planValidator, toCamelCase(rResponse.data))
    }

    async getAll(): Promise<Plan[]> {
        const url = "plan"
        const response = await authRequest(axiosInstance.get, url)
        return safeArrayParsing(planValidator, toCamelCase(response.data))
    }
}