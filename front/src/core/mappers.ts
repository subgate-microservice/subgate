import {Plan, PlanUpdate, Subscription, SubscriptionUpdate} from "./domain.ts";
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


export class SubscriptionMapper{
    toSubUpdate(target: Subscription): SubscriptionUpdate{
        target = recursive(target)
        return {
            autorenew: target.autorenew,
            billingInfo: target.billingInfo,
            discounts: target.discounts,
            fields: target.fields,
            id: target.id,
            pausedFrom: target.pausedFrom,
            planInfo: target.planInfo,
            status: target.status,
            subscriberId: target.subscriberId,
            usages: target.usages,
        }
    }
}