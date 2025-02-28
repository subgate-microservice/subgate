import {createApp} from 'vue'
import App from './App.vue'
import PrimeVue from 'primevue/config';
import Aura from '@primevue/themes/aura';
import {createPinia} from "pinia";
import {router} from "./router.ts";
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';

import {Form} from "@primevue/forms";
import {
    Button,
    DatePicker,
    Card,
    ConfirmDialog,
    Checkbox,
    Dialog,
    IconField,
    InputIcon,
    InputGroup,
    InputNumber,
    InputText,
    IftaLabel,
    Message,
    Panel,
    Select,
    Toast,
    Textarea,
    Toolbar,
} from "primevue";
import {PrimeIcons} from '@primevue/core/api';


import "tailwindcss/tailwind.css"
import 'primeicons/primeicons.css'
import "../assets/my-styles.css"
import {definePreset} from "@primevue/themes";

const pinia = createPinia()

const components = {
    "Button": Button,
    "Card": Card,
    "Checkbox": Checkbox,
    "ConfirmDialog": ConfirmDialog,
    "DatePicker": DatePicker,
    "Dialog": Dialog,
    "IftaLabel": IftaLabel,
    "InputText": InputText,
    "IconField": IconField,
    "InputNumber": InputNumber,
    "InputGroup": InputGroup,
    "Form": Form,
    "Message": Message,
    "Panel": Panel,
    "PrimeIcons": PrimeIcons,
    "Select": Select,
    "Textarea": Textarea,
    "Toast": Toast,
    "Toolbar": Toolbar,
    "InputIcon": InputIcon,
}

const myPreset = definePreset(Aura, {
    semantic: {
        colorScheme: {
            light: {
                surface: {
                    0: 'white',
                    50: '{zinc.50}',
                    100: '{zinc.100}',
                    200: '{zinc.200}',
                    300: '{zinc.300}',
                    400: '{zinc.400}',
                    500: '{zinc.500}',
                    600: '{zinc.600}',
                    700: '{zinc.700}',
                    800: '{zinc.800}',
                    900: '{zinc.900}',
                    950: '{zinc.950}'
                }
            }
        }
    }
})

const app = createApp(App);

for (let [key, value] of Object.entries(components)) {
    app.component(key, value)
}

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: myPreset,
    }
})
app.use(ToastService)
app.use(ConfirmationService)
app.mount("#app")
