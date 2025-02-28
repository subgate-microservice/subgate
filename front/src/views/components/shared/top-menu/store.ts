import {defineStore} from "pinia";
import {ref} from "vue";

export const useTopMenu = defineStore("TopMenu", () => {
    const headerTitle = ref("TEMP_VALUE")
    return {headerTitle}
})