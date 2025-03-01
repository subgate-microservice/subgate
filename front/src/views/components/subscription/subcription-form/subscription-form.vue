<script setup lang="ts">
import {ref, Ref} from "vue";
import {recursive} from "../../../../utils/other.ts";
import {
  SubscriptionCreate,
  SubscriptionUpdate,
} from "../../../../core/domain.ts";
import {blankSubscriptionCreate} from "../../../../core/factories.ts";
import PlanSelector from "./plan-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";
import UsageRateManager from "../../../../core/components/usage-rate-manager.vue";
import StatusSelector from "./status-selector.vue";
import BillingInfo from "./billing-info.vue";


const e = defineEmits<{
  (e: "submit", data: SubscriptionCreate): void,
  (e: "cancel"): void,
}>()

const p = defineProps<{
  initData?: SubscriptionUpdate
}>()
const defaultValue = blankSubscriptionCreate()


const formData: Ref<SubscriptionCreate> = ref(recursive(p.initData) ?? defaultValue)

const validator = ref({discounts: true})


const onSubmit = () => {
  console.log(formData.value)
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
            :init-plan-id="formData.planInfo.id"
            v-model:billing-info="formData.billingInfo"
            v-model:usage-rates="formData.usages"
            v-model:discounts="formData.discounts"
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
            v-model:validated="validator.discounts"
        />
        <usage-rate-manager
            :base-period="formData.billingInfo.billingCycle"
            :usage-rates="formData.usages"
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