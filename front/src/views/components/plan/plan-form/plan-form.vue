<script setup lang="ts">
import {Ref, ref} from 'vue';
import {InputGroup} from "primevue";

import PeriodSelector from "../../../../core/components/period-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";
import UsageRateManager from "../../../../core/components/usage-rate-manager.vue";
import {isEmpty, recursive} from "../../../../utils/other.ts";
import {PlanCreateErrors, PlanCreateValidationResult, validatePlanCreate} from "../../../../core/validators.ts";
import {Period, PlanCreate} from "../../../../core/domain.ts";


interface P {
  initData?: PlanCreate,
}

const p = withDefaults(defineProps<P>(), {
  initData: () => ({
    title: "string",
    price: 100,
    currency: "USD",
    billingCycle: Period.enum.Monthly,
    description: "",
    level: 10,
    features: "",
    usageRates: [],
    fields: {},
    discounts: [],
  })
})

const e = defineEmits<{
  (e: "submit", data: PlanCreate): void,
  (e: "cancel"): void,
}>()


const inputSchema = ref(recursive(p.initData))
const validationResult: Ref<PlanCreateValidationResult> = ref(PlanCreateErrors())


const valid = ref({discounts: true})

const onSubmit = () => {
  validationResult.value = validatePlanCreate(inputSchema.value)
  if (!isEmpty(validationResult.value)) {
    console.log("success")
    // e("submit", data)
  } else {
    console.error(validationResult.value)
  }
};

const onCancel = () => {
  e("cancel")
}
</script>

<template>
  <div class="w-[50rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">

      <!--CoreInformation-->
      <div class="flex flex-col gap-3 flex-1 core-plan-info">
        <IftaLabel>
          <InputText id="title" v-model="inputSchema.title" class="w-full"/>
          <label for="title">Title</label>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.title" class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <IftaLabel>
          <InputNumber id="level" v-model="inputSchema.level" class="w-full"/>
          <label for="period">Level</label>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.level" class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <IftaLabel>
          <Textarea
              id="description"
              v-model="inputSchema.description"
              class="w-full"
              rows="3"
              style="resize: none"
          />
          <label for="description">Description</label>
        </IftaLabel>

        <InputGroup>

          <!--Price-->
          <IftaLabel class="w-1/4">
            <InputNumber id="price" v-model="inputSchema.price" :minFractionDigits="2" :maxFractionDigits="5"/>
            <label for="price">Price</label>
          </IftaLabel>

          <!--Currency-->
          <IftaLabel class="w-1/4">
            <Select
                v-model="inputSchema.currency"
                :options="['USD', 'EUR']"
                placeholder="Currency"
                id="Currency"
            />
            <label for="Currency">Currency</label>
          </IftaLabel>

          <!--BillingCycle-->
          <period-selector v-model="inputSchema.billingCycle" class="w-2/4" label="Billing cycle"/>

        </InputGroup>
        <div class="mt-1">
          <Message
              severity="error" size="small" variant="simple"
              v-for="err in [...validationResult.price, ...validationResult.currency, ...validationResult.billingCycle]"
          >
            {{ err }}
          </Message>
        </div>


      </div>

      <!--Features textarea-->
      <div class="w-full h-[10rem]">
        <IftaLabel class="h-full">
          <Textarea
              id="FeaturesComponent"
              v-model="inputSchema.features"
              style="resize: none;"
              class="w-full h-full"
              placeholder="Enter plan features separated with new line"
          />
          <label for="FeaturesComponent">Features</label>
        </IftaLabel>
      </div>


      <usage-rate-manager :usage-rates="inputSchema.usageRates"/>
      <discount-manager :discounts="inputSchema.discounts" v-model:validated="valid.discounts"/>
      {{ valid.discounts }}

      <div class="flex flex-wrap gap-2">
        <Button
            label="Submit"
            @click="onSubmit"
        />
        <Button
            label="Cancel"
            outlined
            @click="onCancel"
        />
      </div>
    </div>


  </div>

</template>


<style scoped>


</style>