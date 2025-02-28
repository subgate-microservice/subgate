import {browser, Fief} from "@fief/fief";

import {defineStore} from "pinia";
import {Ref, ref} from "vue";
import {FIEF_BASE_URL, FRONTEND_BASE_URL} from "../../config.ts";

export const FIEF_CLIENT_ID = "qsscgXfp53_0LkJoBgzSDRt1TtpkzOWGuWFErBf_dtA"

export const FIEF_CALLBACK_PAGE = `${FRONTEND_BASE_URL}/auth/callback`
export const REDIRECT_AFTER_LOGOUT = `${FRONTEND_BASE_URL}/auth/login`
export const REDIRECT_AFTER_LOGIN = `${FRONTEND_BASE_URL}/plans`


export const fiefClient = new Fief({
    baseURL: FIEF_BASE_URL,
    clientId: FIEF_CLIENT_ID,
})

export const fiefAuth = new browser.FiefAuth(fiefClient)


export const useLoginStore = defineStore(
    "useLoginStore",
    () => {
        const callbackAfterLogin: Ref<(() => void) | null> = ref(null)
        return {callbackAfterLogin}
    }
)


export async function goToFiefLoginPage() {
    console.log("goToFiefLoginPage")
    await fiefAuth.redirectToLogin(FIEF_CALLBACK_PAGE)
}

export async function getDataFromAuthCallback() {
    console.log("getDataFromAuthCallback")
    await fiefAuth.authCallback(FIEF_CALLBACK_PAGE)
    window.location.replace(REDIRECT_AFTER_LOGIN)
}

export async function fiefLogout() {
    await fiefAuth.logout(REDIRECT_AFTER_LOGOUT)
}
