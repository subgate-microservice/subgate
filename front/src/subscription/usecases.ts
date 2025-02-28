import {SubscriptionSby, Subscription, SubscriptionFormData} from "./domain.ts";
import {getSubscriptionGateway} from "./gateways.ts";
import {Id} from "../core.ts";

export async function getSelectedSubscriptions(sby: SubscriptionSby): Promise<Subscription[]> {
    return await getSubscriptionGateway().getSelected(sby)
}

export async function getSubscriptionById(subId: Id): Promise<Subscription> {
    return await getSubscriptionGateway().getOne(subId)
}

export async function createSubscription(data: SubscriptionFormData): Promise<Subscription> {
    return await getSubscriptionGateway().createOne(data)
}

export async function updateSubscription(data: Subscription): Promise<void> {
    await getSubscriptionGateway().updateOne(data)
}

export async function deleteSubscriptionById(subId: string): Promise<void> {
    await getSubscriptionGateway().deleteOne(subId)
}

export async function deleteSelectedSubscriptions(sby: SubscriptionSby): Promise<void> {
    await getSubscriptionGateway().deleteSelected(sby)
}