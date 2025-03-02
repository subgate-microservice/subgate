<script setup lang="ts">
import {ModelRef, onMounted, ref, Ref, watch} from "vue";
import {
  BillingInfo,
  Discount,
  Plan, PlanInfo, UsageRate,
} from "../../domain.ts";
import {PlanRepo} from "../../repositories.ts";
import {recursive} from "../../../utils/other.ts";
import {blankBillingInfo, blankPlanInfo, usageFromUsageRate} from "../../factories.ts";

const p = defineProps<{
  initPlanId?: string,
}>()


const selectedPlan: Ref<Plan | null> = ref(null)
const usageRateModel: ModelRef<UsageRate[]> = defineModel("usageRates", {default: () => []})
const discountModel: ModelRef<Discount[]> = defineModel("discounts", {default: () => []})
const billingInfoModel: ModelRef<BillingInfo> = defineModel("billingInfo", {default: () => blankBillingInfo()})
const planInfoModel: ModelRef<PlanInfo> = defineModel("planInfo", {default: () => blankPlanInfo()})

watch(selectedPlan, () => {
  if (selectedPlan.value) {
    discountModel.value = recursive(selectedPlan.value.discounts)
    usageRateModel.value = selectedPlan.value.usageRates.map(item => usageFromUsageRate(item))
    billingInfoModel.value = {
      billingCycle: selectedPlan.value.billingCycle,
      currency: selectedPlan.value.currency,
      lastBilling: new Date(),
      price: selectedPlan.value.price,
      savedDays: 0,
    }
    planInfoModel.value = {
      id: selectedPlan.value.id,
      title: selectedPlan.value.title,
      description: selectedPlan.value.description,
      features: selectedPlan.value.features,
      level: selectedPlan.value.level,
    }
  }
})

const allPlans: Ref<Plan[]> = ref([])

onMounted(async () => {
  allPlans.value = await new PlanRepo().getAll()
  if (p.initPlanId) {
    const target = allPlans.value.find(item => item.id === p.initPlanId)
    if (target
        && target.title === planInfoModel.value.title
        && target.level == planInfoModel.value.level
        && target.description == planInfoModel.value.description
        && target.features === planInfoModel.value.features

        && target.price === billingInfoModel.value.price
        && target.currency === billingInfoModel.value.currency
        && target.billingCycle === billingInfoModel.value.billingCycle
    ) {
      selectedPlan.value = target
    }
  } else {
    if (allPlans.value.length > 0) {
      selectedPlan.value = allPlans.value[0]
    }
  }
})

</script>

<template>
  <div>
    <IftaLabel>
      <Select
          id="PlanSelector"
          option-label="title"
          v-model="selectedPlan"
          :options="allPlans"
          class="w-full"
      />
      <label for="PlanSelector">Plan</label>
    </IftaLabel>


  </div>
</template>

<style scoped>

</style>