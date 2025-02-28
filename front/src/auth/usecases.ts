import {ApikeyFormData, UpdateEmailForm, UpdatePasswordForm} from "./domain.ts";
import {getApikeyGateway, getAuthGateway} from "./gateways.ts";

export async function goToLogin() {
    await getAuthGateway().login()
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

}

export function getCurrentAuthNullable() {
    return getAuthGateway().getCurrentAuth()
}

export function getCurrentAuth() {
    const user = getCurrentAuthNullable()
    if (!user) throw Error("CurrentUser is null")
    return user
}

export function isAuthenticated() {
    return getCurrentAuthNullable() !== null
}

export function getAllApikeys() {
    return getApikeyGateway().getAll()
}

export function createApikey(data: ApikeyFormData) {
    return getApikeyGateway().createOne(data)
}

export function deleteApikeyById(id: string) {
    return getApikeyGateway().deleteOneById(id)
}