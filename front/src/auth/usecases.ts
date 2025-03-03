import {UpdateEmailForm, UpdatePasswordForm} from "./domain.ts";
import {getAuthGateway, useAuthStore} from "./gateways.ts";


export async function login(login: string, password: string) {
    await getAuthGateway().login(login, password)
}

export async function logout() {
    await getAuthGateway().logout()
    const event = new Event("logout")
    window.dispatchEvent(event)
}

export async function updateEmail(data: UpdateEmailForm) {
    await getAuthGateway().updateEmail(data)
}

export async function verifyEmail(verificationCode: string) {
    await getAuthGateway().verifyEmail(verificationCode)
}

export async function updatePassword(data: UpdatePasswordForm) {
    if (data.newPassword !== data.repeatPassword) throw Error("New password and repeat password are not the same")
    await getAuthGateway().updatePassword(data)
}

export async function deleteAccount() {
    throw Error("NotImpl")
}


export function isAuthenticated() {
    return useAuthStore().myself !== null
}

