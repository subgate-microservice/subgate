import {useValidator, Validator} from "../../../utils/validator.ts";
import {webhookCUValidator, webhookValidator} from "../../validators.ts";
import {ZodError} from "zod";
import {WebhookCU} from "../../domain.ts";
import {Ref} from "vue";

export function createWebhookCUFormValidator(formData: Ref<WebhookCU>): Validator {
    const validator = useValidator(formData)
    validator.addFieldValidator(
        "targetUrl",
        (value) => {
            try {
                webhookCUValidator.shape.targetUrl.parse(value)
                return []
            } catch (err) {
                if (err instanceof ZodError) {
                    return err.errors.map((e) => e.message)
                }
                return [String(err)]
            }
        }
    )
    validator.addFieldValidator(
        "eventCode",
        (value) => {
            try {
                webhookCUValidator.shape.eventCode.parse(value)
                return []
            } catch (err) {
                if (err instanceof ZodError) {
                    return err.errors.map((e) => e.message)
                }
                return [String(err)]
            }
        }
    )
    return validator
}