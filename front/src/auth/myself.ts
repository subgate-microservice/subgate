import {AuthUser, EmailUpdate, LoginData, PasswordUpdate} from "./domain.ts";
import {axiosInstance} from "../axios-instanse.ts";
import {defineStore} from "pinia";
import {computed, ref, Ref} from "vue";
import {safeParsing} from "../shared/services/other.ts";
import {authUserValidator} from "./validators.ts";


export const useAuthStore = defineStore("useAuthStore", () => {
    const myself: Ref<AuthUser | null> = ref(null)

    async function loadMyself() {
        const url = "/users/me"
        const response = await axiosInstance.get(url)
        myself.value = safeParsing(authUserValidator, {id: response.data.id, email: response.data.email})
    }

    async function updateEmail(data: EmailUpdate) {
        console.log("updateEmail", data)
        throw Error("NotImpl")
    }

    async function verifyEmail(code: string) {
        console.log("verifyEmail", code)
        throw Error("NotImpl")
    }

    async function updatePassword(data: PasswordUpdate) {
        console.log("updatePassword", data)
        throw Error("NotImpl")
    }

    async function login(loginData: LoginData) {
        const url = `/auth/jwt/login`
        const headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        const data = new URLSearchParams();
        data.append("grant_type", "password")
        data.append("username", loginData.username)
        data.append("password", loginData.password)
        await axiosInstance.post(url, data, {headers})
    }

    async function logout() {
        console.log("logout")
    }

    async function deleteAccount() {
        throw Error("NotImpl")
    }


    return {
        isAuthenticated: computed(() => !!myself.value),
        loadMyself,
        updateEmail,
        updatePassword,
        verifyEmail,
        login,
        logout,
        deleteAccount,
    }
})
