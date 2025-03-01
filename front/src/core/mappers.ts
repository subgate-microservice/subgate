import {Plan, PlanUpdate} from "./domain.ts";
import {recursive} from "../utils/other.ts";

export class PlanMapper {

    toPlanUpdate(target: Plan): PlanUpdate {
        target = recursive(target)
        return {
            billingCycle: target.billingCycle,
            currency: target.currency,
            description: target.description,
            discounts: target.discounts,
            features: target.features,
            fields: target.fields,
            id: target.id,
            level: target.level,
            price: target.price,
            title: target.title,
            usageRates: target.usageRates,
        }
    }
}