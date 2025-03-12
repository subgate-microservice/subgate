import {createRouter, createWebHistory} from "vue-router"
import MyPlans from "./subscription/pages/my-plans.vue";
import MySubscriptions from "./subscription/pages/my-subscriptions.vue";
import MyWebhooks from "./webhook/pages/my-webhooks.vue";
import MyApikeys from "./apikey/pages/my-apikeys.vue";
import FastapiLogin from "./auth/pages/fastapi-login.vue";
import {useAuthStore} from "./auth/myself.ts";
import MyProfile from "./auth/pages/my-profile.vue";
import MyRegister from "./auth/pages/my-register.vue";


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
                {
                    path: "register",
                    component: MyRegister,
                    name: "Register",
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
            path: "/profile",
            children: [
                {
                    path: "",
                    component: MyProfile,
                    name: "Profile",
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
    const auth = useAuthStore()
    // Незалогиненный пользователь на странице сайта => отправить на страницу логина
    if (!publicRoutes.has(to.name as string) && !auth.isAuthenticated) {
        try {
            await auth.loadMyself()
            return
        } catch (err) {
            return {name: "Login"}
        }
    }

    // Залогиненный пользователь на странице логина => отправить на главную
    if (publicRoutes.has(to.name as string) && auth.isAuthenticated) {
        return {name: "Plans"}
    }
})
