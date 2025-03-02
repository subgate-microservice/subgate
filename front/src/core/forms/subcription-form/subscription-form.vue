<script setup lang="ts">
import {ref, Ref} from "vue";
import {recursive} from "../../../utils/other.ts";
import {
  SubscriptionUpdate,
} from "../../domain.ts";
import {blankSubscriptionForm} from "../../factories.ts";
import PlanSelector from "./plan-selector.vue";
import DiscountManager from "../../components/discount-manager.vue";
import UsageRateManager from "../../components/usage-rate-manager.vue";
import StatusSelector from "./status-selector.vue";
import BillingInfo from "./billing-info.vue";


const e = defineEmits<{
  (e: "submit", data: SubscriptionUpdate): void,
  (e: "cancel"): void,
}>()

const p = defineProps<{
  initData?: SubscriptionUpdate
  mode: "create" | "update",
}>()
const defaultValue = blankSubscriptionForm()


const formData: Ref<SubscriptionUpdate> = ref(recursive(p.initData) ?? defaultValue)

const valid = ref({discounts: true, usages: true})
const showValidationErrors = ref(false)

const onSubmit = () => {
  const isValidated = Object.values(valid.value).every(v => v)
  if (isValidated) {
    e("submit", formData.value)
    showValidationErrors.value = false
  } else {
    showValidationErrors.value = true
  }
};

const onCancel = () => {
  e("cancel")
}

</script>

<template>
  <div class="w-[50rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">

      <div class="flex flex-col gap-3 flex-1 core-plan-info">
        <IftaLabel>
          <InputText id="subscriberId" v-model="formData.subscriberId" class="w-full"/>
          <label for="subscriberId">Subscriber ID</label>
        </IftaLabel>

        <plan-selector
            :init-plan-id="p.mode === 'update' ? formData.planInfo.id : undefined"
            v-model:billing-info="formData.billingInfo"
            v-model:usage-rates="formData.usages"
            v-model:discounts="formData.discounts"
            v-model:plan-info="formData.planInfo"
        />

        <status-selector
            v-model:status="formData.status"
            v-model:paused-from="formData.pausedFrom"
        />

        <billing-info
            v-model:price="formData.billingInfo.price"
            v-model:currency="formData.billingInfo.currency"
            v-model:billing-cycle="formData.billingInfo.billingCycle"
        />

        <discount-manager
            :discounts="formData.discounts"
            v-model:validated="valid.discounts"
        />
        <usage-rate-manager
            :show-errors="showValidationErrors"
            :base-period="formData.billingInfo.billingCycle"
            v-model:usage-rates="formData.usages"
            v-model:validated="valid.usages"
        />

        <!--Navigate-->
        <div class="flex flex-wrap gap-2 mt-4">
          <Button
              label="Submit"
              @click="onSubmit"
          />
          <Button
              label="Cancel"
              @click="onCancel"
              outlined
          />
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>

</style>