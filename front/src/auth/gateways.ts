import {Apikey, ApikeyFormData, AuthUser, UpdateEmailForm, UpdatePasswordForm} from "./domain.ts";
import {getAsNotNullable, safeArrayParsing, safeParsing} from "../utils/other.ts";
import {fiefAuth, fiefClient, goToFiefLoginPage, fiefLogout} from "./fief.ts";
import {v4} from "uuid";
import {authRequest} from "./auth-request.ts";
import {axiosInstance} from "../axios-instanse.ts";


class AuthGateway {
    getCurrentAuth(): AuthUser | null {
        const userinfo = fiefAuth.getUserinfo()
        if (userinfo === null) return null
        return safeParsing(AuthUser, {id: userinfo.sub, email: userinfo.email})
    }

    async updateEmail(data: UpdateEmailForm) {
        const tokenInfo = getAsNotNullable(fiefAuth.getTokenInfo())
        await fiefClient.emailChange(tokenInfo.access_token, data.email)
    }

    async verifyEmail(code: string) {
        const tokenInfo = getAsNotNullable(fiefAuth.getTokenInfo())
        await fiefClient.emailVerify(tokenInfo.access_token, code)
    }

    async updatePassword(data: UpdatePasswordForm) {
        const tokenInfo = getAsNotNullable(fiefAuth.getTokenInfo())
        await fiefClient.changePassword(tokenInfo.access_token, data.newPassword)
    }

    async login() {
        await goToFiefLoginPage()
    }

    async logout() {
        await fiefLogout()
    }
}

export class FakeAuthGateway extends AuthGateway {
    private readonly currentUser: AuthUser;
    private loggedIn: boolean

    constructor() {
        super()
        this.currentUser = {id: "91a517f0-6d78-4fe9-acaa-ac10fa8f139b", email: "fake@gmail.com"}
        this.loggedIn = true
    }

    getCurrentAuth(): AuthUser | null {
        return this.loggedIn ? {...this.currentUser} : null
    }

    async updateEmail(data: UpdateEmailForm): Promise<void> {
        console.log(data)
    }

    async verifyEmail(code: string): Promise<void> {
        console.log(code)
    }

    async updatePassword(data: UpdatePasswordForm): Promise<void> {
        console.log(data)
    }

    async login() {
        this.loggedIn = true
    }

    async logout(): Promise<void> {
        this.loggedIn = false
    }
}

export function getAuthGateway() {
    return new AuthGateway()
}


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