import {EventCode} from "../../../../other/event-code";
import {WebhookFormData} from "../../../../webhook";


export interface EventCodeItem {
    name: string,
    code: string,
    value: EventCode,
}

export interface InputSchema {
    targetUrl: string,
    selectedEvent: EventCodeItem,
}

export interface ValidationResult {
    targetUrl: string[],
    validated: boolean,
}

export function blankValidationResult(): ValidationResult {
    return {
        targetUrl: [],
        validated: true,
    }
}

export function convertInputSchemaToWebhookFormData(schema: InputSchema): WebhookFormData {
    return {
        targetUrl: schema.targetUrl,
        eventCode: schema.selectedEvent.value,
    }
}

export function convertWebhookFormDataToInputSchema(data: WebhookFormData): InputSchema {
    return {
        targetUrl: data.targetUrl,
        selectedEvent: {name: data.eventCode, code: data.eventCode, value: data.eventCode},
    }
}


export function  validateInputSchema(schema: InputSchema): ValidationResult{
    const result: ValidationResult = {
        targetUrl: [],
        validated: true,
    }
    if (!schema.targetUrl) {
        result.targetUrl.push("Target url should be a valid url")
    }
    return result
}