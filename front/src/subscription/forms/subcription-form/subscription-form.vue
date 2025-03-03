<script setup lang="ts">
import {ref, Ref} from "vue";
import {recursive} from "../../../shared/services/other.ts";
import {
  SubscriptionCU,
} from "../../domain.ts";
import {blankSubscriptionCU} from "../../factories.ts";
import PlanSelector from "./plan-selector.vue";
import DiscountManager from "../../components/discount-manager.vue";
import UsageRateManager from "../../components/usage-rate-manager.vue";
import StatusSelector from "./status-selector.vue";
import BillingInfo from "./billing-info.vue";
import {useValidatorService} from "../../../shared/services/validation-service.ts";
import {subscriptionCUValidator} from "../../validators.ts";


const e = defineEmits<{
  (e: "submit", data: SubscriptionCU): void,
  (e: "cancel"): void,
}>()

const p = defineProps<{
  initData?: SubscriptionCU
  mode: "create" | "update",
}>()

const formData: Ref<SubscriptionCU> = ref(recursive(p.initData) ?? blankSubscriptionCU())
const validator = useValidatorService(formData, subscriptionCUValidator)

const onSubmit = () => {
  validator.validate()
  if (validator.isValidated) {
    e("submit", formData.value)
  } else {
    console.warn(validator.getAllErrors())
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
          <InputText
              id="subscriberId"
              v-model="formData.subscriberId"
              class="w-full"
          />
          <label for="subscriberId">Subscriber ID</label>
          <Message
              severity="error"
              class="mt-1"
              size="small"
              v-for="err in validator.getFieldErrors('subscriberId')"
          >
            {{ err }}
          </Message>
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
            v-model:discounts="formData.discounts"
            :validator="validator"
            field-prefix="discounts"
        />

        <usage-rate-manager
            :base-period="formData.billingInfo.billingCycle"
            :validator="validator"
            field-prefix="usages"
            item-type="usage"
            v-model:usage-rates="formData.usages"
        />

        <!--Navigate-->
        <div class="flex flex-wrap gap-2 mt-4">
          <Button label="Submit" @click="onSubmit"/>
          <Button label="Cancel" @click="onCancel" outlined/>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>

</style>