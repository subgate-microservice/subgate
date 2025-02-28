import {ApikeyFormData} from "../../../../auth";

export interface ValidationResults{
    title: string[],
    validated: boolean,
}

export function validateApikeyFormData(schema: ApikeyFormData) : ValidationResults{
    const result: ValidationResults = {title: [], validated: true,}
    if (schema.title.length < 5) {
        result.title.push("Title must contains at least 5 symbols")
        result.validated = false
    }
    return result
}