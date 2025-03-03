<script setup lang="ts">
import {Ref, ref} from 'vue';
import {InputGroup} from "primevue";
import PeriodSelector from "../components/period-selector.vue";
import DiscountManager from "../components/discount-manager.vue";
import UsageRateManager from "../components/usage-rate-manager.vue";
import {recursive} from "../../utils/other.ts";
import {PlanCU} from "../domain.ts";
import {planCUValidator} from "../validators.ts";
import {useValidatorService} from "../../utils/validation-service.ts";
import {blankPlanCU} from "../factories.ts";

interface Props {
  initData?: PlanCU;
}

const props = defineProps<Props>();
const emit = defineEmits(["submit", "cancel"]);


const formData: Ref<PlanCU> = ref(recursive(props.initData) ?? blankPlanCU())

const validator = useValidatorService(formData, planCUValidator)

const onSubmit = () => {
  validator.validate()
  if (validator.isValidated) {
    emit("submit", formData.value)
  } else {
    console.warn(validator.getAllErrors())
  }
}
</script>

<template>
  <div class="w-[50rem] h-full flex flex-wrap gap-4">
    <div class="flex flex-col gap-3 flex-1">
      <IftaLabel>
        <InputText v-model="formData.title" class="w-full"/>
        <label>Title</label>
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('title')"
        >
          {{ err }}
        </Message>
      </IftaLabel>

      <IftaLabel>
        <InputNumber v-model="formData.level" class="w-full" :min="0"/>
        <label>Level</label>
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('level')"
        >
          {{ err }}
        </Message>
      </IftaLabel>

      <IftaLabel>
        <Textarea v-model="formData.description" class="w-full" rows="3" style="resize: none"/>
        <label>Description</label>
      </IftaLabel>

      <InputGroup>
        <IftaLabel class="w-1/4">
          <InputNumber v-model="formData.price" :minFractionDigits="2" :maxFractionDigits="5" :min="0"/>
          <label>Price</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <Select v-model="formData.currency" :options="['USD', 'EUR']" placeholder="Currency"/>
          <label>Currency</label>
        </IftaLabel>

        <PeriodSelector v-model="formData.billingCycle" class="w-2/4" label="Billing cycle"/>
      </InputGroup>

    </div>

    <IftaLabel class="w-full h-[10rem]">
      <Textarea v-model="formData.features" class="w-full h-full" placeholder="Enter features, one per line"
                style="resize: none" rows="3"/>
      <label>Features</label>
    </IftaLabel>

    <UsageRateManager
        v-model:usage-rates="formData.usageRates"
        :base-period="formData.billingCycle"
        :validator="validator"
        field-prefix="usageRates"
    />
    <DiscountManager
        v-model:discounts="formData.discounts"
        :validator="validator"
        field-prefix="discounts"
    />

    <div class="flex flex-wrap gap-2">
      <Button label="Submit" @click="onSubmit"/>
      <Button label="Cancel" outlined @click="$emit('cancel')"/>
    </div>
  </div>
</template>
