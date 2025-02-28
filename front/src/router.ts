import {createRouter, createWebHistory} from "vue-router"
import MyPlans from "./views/pages/my-plans.vue";
import {goToLogin, isAuthenticated} from "./auth";
import MySubscriptions from "./views/pages/my-subscriptions.vue";
import MyWebhooks from "./views/pages/my-webhooks.vue";
import MyAccount from "./views/pages/my-account.vue";
import MyApikeys from "./views/pages/my-apikeys.vue";
import FiefCallback from "./views/pages/fief-callback.vue";
import FiefLogin from "./views/pages/fief-login.vue";


export const router = createRouter({
    history: createWebHistory(),
    linkActiveClass: 'active',
    routes: [
        {
            path: "/auth",
            children: [
                {
                    path: "callback",
                    component: FiefCallback,
                    name: "OauthCallback",
                },
                {
                    path: "login",
                    component: FiefLogin,
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
        await goToLogin()
        return
    }

    // Залогиненный пользователь на странице логина => отправить на главную
    if (publicRoutes.has(to.name as string) && isAuthenticated()) {
        return {name: "Plans"}
    }
})
