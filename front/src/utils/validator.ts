import { reactive, computed, Ref } from 'vue';
import { ZodObject } from 'zod';

export interface Validator {
    isShow: Ref<boolean>;
    isValidated: Ref<boolean>;
    validate: () => void;
    getErrors: (field: string) => string[];
    addFieldValidator: (field: string, validator: (v: any) => string[]) => void;
    addZodValidator: (validator: ZodObject<any>) => void;
}

export function useValidator<T>(formData: Ref<T>): Validator {
    const fieldValidators: Record<string, ((value: any) => string[])[]> = reactive({});
    const errors: Record<string, string[]> = reactive({});
    let zodValidator: (() => void) | null = null;

    function addFieldValidator(field: string, validator: (v: any) => string[]) {
        if (!fieldValidators[field]) fieldValidators[field] = [];
        fieldValidators[field].push(validator);
    }

    function addZodValidator(validator: ZodObject<any>) {
        zodValidator = () => {
            const result = validator.safeParse(formData.value);
            if (!result.success) {
                errorsClear();
                result.error.errors.forEach(({ path, message }) => {
                    if (path.length > 0) {
                        const field = path[0];
                        if (!errors[field]) errors[field] = [];
                        errors[field].push(message);
                    }
                });
            }
        };
    }

    function errorsClear() {
        Object.keys(errors).forEach(key => delete errors[key]);
    }

    function validate() {
        errorsClear();
        Object.entries(fieldValidators).forEach(([field, validators]) => {
            const fieldErrors = validators.flatMap(validator => validator(formData.value[field]));
            if (fieldErrors.length) {
                errors[field] = fieldErrors;
            }
        });
        if (zodValidator) zodValidator();
    }

    const isShow = computed(() => Object.keys(errors).length > 0);
    const isValidated = computed(() => Object.keys(errors).length === 0);

    return {
        isShow,
        isValidated,
        validate,
        getErrors: (field) => errors[field] || [],
        addFieldValidator,
        addZodValidator,
    };
}
