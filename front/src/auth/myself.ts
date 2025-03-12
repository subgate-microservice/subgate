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
        myself.value = safeParsing(authUserValidator, {id: response.data.id})
    }

    async function updateEmail(data: EmailUpdate) {
        const url = "users/me/update-email"
        const payload = {new_email: data.email, password: data.password}
        await axiosInstance.patch(url, payload)
    }

    async function verifyEmail(code: string) {
        console.log(code)
        throw Error("NotImpl")
    }

    async function updatePassword(data: PasswordUpdate) {
        const url = "users/me/update-password"
        const payload = {old_password: data.oldPassword, new_password: data.newPassword}
        await axiosInstance.patch(url, payload, {})
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
        const url = "/auth/jwt/logout"
        await axiosInstance.post(url);
        sessionStorage.removeItem("fastapiusersauth")
        myself.value = null
    }

    async function deleteAccount(password: string) {
        const url = "/users/me"
        const data = {password: password}
        await axiosInstance.delete(url, {data})
        sessionStorage.removeItem("fastapiusersauth")
        myself.value = null
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
