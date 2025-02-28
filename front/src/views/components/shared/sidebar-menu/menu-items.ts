import {MenuItem} from "primevue/menuitem";
import {router} from "../../../../router.ts";

export const menuItems: MenuItem[] = [
    {
        label: "Plans",
        command: () => router.push({name: "Plans"}),
    },
    {
        label: "Subscriptions",
        command: () => router.push({name: "Subscriptions"}),
    },
    {
        label: "Webhooks",
        command: () => router.push({name: "Webhooks"}),
    },
    {
        label: "Apikeys",
        command: () => router.push({name: "Apikeys"}),
    },
]