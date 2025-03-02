import {reactive, Ref, ref, watch} from "vue";
import {ZodError, ZodSchema} from "zod";

interface ValidationState {
    errors: Ref<Record<string, string>>;
    isShowErrors: Ref<boolean>;
    isValidated: Ref<boolean>;
    validate: () => void;
}

export function useValidationService<T>(
    formData: Ref<T>,
    validators: Record<string, ZodSchema<any>>,
    validateOnChange = false
): ValidationState {
    const errors = ref<Record<string, string>>({});
    const valid = Object.fromEntries(Object.keys(validators).map((key) => [key, true]))

    const isShowErrors = ref(false)
    const isValidated = ref(false)

    const validateField = (key: string): boolean => {
        if (!validators[key]) return true;
        try {
            validators[key].parse(formData.value[key])
            valid[key] = true
        } catch (err) {
            if (err instanceof ZodError) {
                errors.value[key] = err.errors.map((e) => e.message).join(", ")
                valid[key] = false
            }
        }
        return valid[key]
    };

    const validate = () => {
        errors.value = {}
        Object.keys(validators).forEach(validateField)

        isValidated.value = Object.values(valid).every(v => v)
        isShowErrors.value = !isValidated.value
    }

    if (validateOnChange) {
        watch(formData, validate, {deep: true, immediate: true});
    }

    return reactive({validate, isShowErrors, isValidated, errors})
}
