import {Apikey, ApikeyFormData, AuthUser, UpdateEmailForm, UpdatePasswordForm} from "./domain.ts";
import {safeArrayParsing, safeParsing} from "../utils/other.ts";
import {v4} from "uuid";
import {authRequest} from "./auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {defineStore} from "pinia";
import {ref, Ref} from "vue";


class AuthGateway {
    async getMyself(): Promise<AuthUser> {
        const url = "/users/me"
        const response = await axiosInstance.get(url)
        return AuthUser.parse({id: response.data.id, email: response.data.email})
    }

    async updateEmail(data: UpdateEmailForm) {
        console.log("updateEmail", data)
    }

    async verifyEmail(code: string) {
        console.log("verifyEmail", code)
    }

    async updatePassword(data: UpdatePasswordForm) {
        console.log("updatePassword", data)
    }

    async login(username: string, password: string) {
        console.log("login")
        const url = `/auth/jwt/login`
        const headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        const data = new URLSearchParams();
        data.append("grant_type", "password")
        data.append("username", username)
        data.append("password", password)
        data.append("scope", "")
        data.append("scope", "");
        data.append("client_id", "");
        data.append("client_secret", "");
        await axiosInstance.post(url, data, {headers})
    }

    async logout() {
        console.log("logout")
    }
}

export function getAuthGateway(): AuthGateway {
    return new AuthGateway()
}


export const useAuthStore = defineStore("useAuthStore", () => {
    const myself: Ref<AuthUser | null> = ref(null)


    return {
        myself
    }
})

class ApikeyGateway {
    async getAll(): Promise<Apikey[]> {
        return [
            {id: "1", title: "Fake1", createdAt: new Date()},
            {id: "2", title: "Fake2", createdAt: new Date()},
            {id: "3", title: "Fake3", createdAt: new Date()},
        ]
    }

    async createOne(data: ApikeyFormData): Promise<[Apikey, string]> {
        return [{id: v4(), title: data.title, createdAt: new Date()}, v4()]
    }

    async deleteOneById(id: string): Promise<void> {
        console.log(id)
    }
}

class ApikeyGatewayReal extends ApikeyGateway {
    async getAll(): Promise<Apikey[]> {
        const url = `/apikey`
        const response: Apikey[] = (await authRequest(axiosInstance.get, url)).data
        return safeArrayParsing(Apikey, response)
    }

    async createOne(data: ApikeyFormData): Promise<[Apikey, string]> {
        const url = `/apikey`
        const response: [Apikey, string] = (await authRequest(axiosInstance.post, url, data)).data
        return [safeParsing(Apikey, response[0]), response[1]]
    }

    async deleteOneById(id: string): Promise<void> {
        const url = `/apikey/${id}`
        await authRequest(axiosInstance.delete, url)
    }
}

export function getApikeyGateway() {
    return new ApikeyGatewayReal()
}