import {reactive, Ref} from 'vue'
import {ZodObject} from "zod";

export interface ValidationService {
    isValidated: boolean
    validate: () => void
    getFieldErrors: (field: string) => string[]
    getAllErrors: () => string[]
}

export function useValidatorService<T>(formData: Ref<T>, validator: ZodObject<any>): ValidationService {
    const errors = reactive<Record<string, string[]>>({})

    function validate() {
        Object.keys(errors).forEach(key => delete errors[key])

        const result = validator.safeParse(formData.value)
        if (!result.success) {
            result.error.errors.forEach(error => {
                const field = error.path.join(".")
                if (!errors[field]) errors[field] = []
                errors[field].push(error.message)
            });
        }
    }

    function getFieldErrors(field: string): string[] {
        return errors[field] ?? []
    }

    function getAllErrors() {
        return Object.values(errors).flat()
    }

    return {
        get isValidated() {
            return Object.keys(errors).length === 0
        },
        validate,
        getFieldErrors,
        getAllErrors,
    }
}
