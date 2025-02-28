import {Plan, PlanFormData, PlanSby} from "./domain.ts";
import {getPlanGateway} from "./gateways.ts";
import {Id} from "../core.ts";

export async function getPlanById(id: string): Promise<Plan> {
    return await getPlanGateway().getOneById(id)
}

export async function getSelectedPlans(sby: PlanSby): Promise<Plan[]> {
    return await getPlanGateway().getSelected(sby)
}

export async function updatePlan(data: Plan) {
    await getPlanGateway().updateOne(data)
}

export async function deletePlanById(planId: Id) {
    await getPlanGateway().deleteOne(planId)
}

export async function deleteSelectedPlans(sby: PlanSby) {
    await getPlanGateway().deleteSelected(sby)
}


export async function createPlan(data: PlanFormData): Promise<Plan> {
    return await getPlanGateway().createOne(data)
}