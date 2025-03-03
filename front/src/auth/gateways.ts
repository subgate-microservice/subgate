import {AuthUser, UpdateEmailForm, UpdatePasswordForm} from "./domain.ts";
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
        throw Error("NotImpl")
    }

    async verifyEmail(code: string) {
        console.log("verifyEmail", code)
        throw Error("NotImpl")
    }

    async updatePassword(data: UpdatePasswordForm) {
        console.log("updatePassword", data)
        throw Error("NotImpl")
    }

    async login(username: string, password: string) {
        const url = `/auth/jwt/login`
        const headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        const data = new URLSearchParams();
        data.append("grant_type", "password")
        data.append("username", username)
        data.append("password", password)
        await axiosInstance.post(url, data, {headers})
    }

    async logout() {
        console.log("logout")
        throw Error("NotImpl")
    }
}

export function getAuthGateway(): AuthGateway {
    return new AuthGateway()
}


export const useAuthStore = defineStore("useAuthStore", () => {
    const myself: Ref<AuthUser | null> = ref(null)

    window.addEventListener("logout", () => myself.value = null)

    return {
        myself
    }
})
