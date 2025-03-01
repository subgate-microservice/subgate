import {reactive} from "vue";

export function useCreateDialogManager() {
    const state = reactive({showFlag: false})

    const openDialog = () => state.showFlag = true
    const closeDialog = () => state.showFlag = false

    return {state, openDialog, closeDialog}
}

export function useUpdateDialogManager<T>() {
    interface State {
        target: T | null
        showFlag: boolean
    }

    const state: State = reactive({showFlag: false, target: null})

    const startUpdate = (item: T) => {
        state.target = item
        state.showFlag = true
    }

    const finishUpdate = () => {
        state.target = null
        state.showFlag = false
    }
    return {
        state,
        startUpdate,
        finishUpdate,
    }
}