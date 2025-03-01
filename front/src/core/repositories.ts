import {Plan, PlanCreate, PlanUpdate} from "./domain.ts";
import {safeArrayParsing, safeParsing, toCamelCase, toSnakeCase} from "../utils/other.ts";
import {authRequest} from "../auth/auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {planValidator} from "./validators.ts";

export class PlanRepo {
    async create(item: PlanCreate): Promise<Plan> {
        const url = "/plan"
        const data = toSnakeCase(item)
        const response = await authRequest(axiosInstance.post, url, data)
        return await this.getById(response.data)
    }

    async update(item: PlanUpdate): Promise<Plan> {
        const url = `/plan/${item.id}`
        const data = toSnakeCase(item)
        await authRequest(axiosInstance.put, url, data)
        return await this.getById(item.id)
    }

    async getAll(): Promise<Plan[]> {
        const url = "plan"
        const response = await authRequest(axiosInstance.get, url)
        return safeArrayParsing(planValidator, toCamelCase(response.data))
    }

    async getById(planId: string): Promise<Plan> {
        const url = `/plan/${planId}`
        const response = await authRequest(axiosInstance.get, url)
        return safeParsing(planValidator, toCamelCase(response.data))
    }
}