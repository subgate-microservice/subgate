import {createRouter, createWebHistory} from "vue-router"
import MyPlans from "./views/pages/my-plans.vue";
import {isAuthenticated} from "./auth";
import MySubscriptions from "./views/pages/my-subscriptions.vue";
import MyWebhooks from "./views/pages/my-webhooks.vue";
import MyAccount from "./views/pages/my-account.vue";
import MyApikeys from "./views/pages/my-apikeys.vue";
import FastapiLogin from "./views/pages/fastapi-login.vue";
import {getAuthGateway} from "./auth/gateways.ts";


export const router = createRouter({
    history: createWebHistory(),
    linkActiveClass: 'active',
    routes: [
        {
            path: "/auth",
            children: [
                {
                    path: "login",
                    component: FastapiLogin,
                    name: "Login",
                },
            ]
        },
        {
            path: "/plans",
            children: [
                {
                    path: "",
                    component: MyPlans,
                    name: "Plans",
                },
            ]
        },
        {
            path: "/subscriptions",
            children: [
                {
                    path: "",
                    component: MySubscriptions,
                    name: "Subscriptions",
                },
            ]
        },
        {
            path: "/webhooks",
            children: [
                {
                    path: "",
                    component: MyWebhooks,
                    name: "Webhooks",
                },
            ]
        },
        {
            path: "/account",
            children: [
                {
                    path: "",
                    component: MyAccount,
                    name: "Account",
                },
            ]
        },
        {
            path: "/apikeys",
            children: [
                {
                    path: "",
                    component: MyApikeys,
                    name: "Apikeys",
                },
            ]
        },
    ],
})

const publicRoutes: Set<string> = new Set(["Login", "Register", "OauthCallback"])


router.beforeEach(async (to,) => {

    // Незалогиненный пользователь на странице сайта => отправить на страницу логина
    if (!publicRoutes.has(to.name as string) && !isAuthenticated()) {
        try {
            await getAuthGateway().preloadAuth()
        } catch (err) {
            return {name: "Login"}
        }
        return
    }

    // Залогиненный пользователь на странице логина => отправить на главную
    if (publicRoutes.has(to.name as string) && isAuthenticated()) {
        return {name: "Plans"}
    }
})
