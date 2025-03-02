import {reactive, computed, Ref} from 'vue'
import {ZodObject} from "zod";

export interface Validator {
    isShow: boolean
    isValidated: boolean
    validate: () => void
    getErrors: (field: string) => string[]
    addFieldValidator: (field: string, validator: (v: any) => string[]) => void
    addZodValidator: (validator: ZodObject<any>) => void,
}

export function useValidator<T>(formData: Ref<T>): Validator {
    const fieldValidators: Record<string, ((value: any) => string[])[]> = reactive({})
    const errors: Record<string, string[]> = reactive({})

    function addFieldValidator(field: string, validator: (v: any) => string[]) {
        if (!fieldValidators[field]) fieldValidators[field] = []
        fieldValidators[field].push(validator)
    }

    function validate() {
        Object.keys(fieldValidators).forEach(field => {
            const validators = fieldValidators[field]
            const fieldErrors = validators.flatMap(validator => validator(formData.value[field]))
            if (fieldErrors.length) {
                errors[field] = fieldErrors
            } else {
                delete errors[field]
            }
        })
    }

    return {
        isShow: computed(() => Object.keys(errors).length > 0),
        isValidated: computed(() => Object.keys(errors).length === 0),
        validate,
        getErrors: (field) => errors[field] || [],
        addFieldValidator,
    }
}

