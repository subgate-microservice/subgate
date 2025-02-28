<script setup lang="ts">
import {Ref, ref} from 'vue';
import {Discount, PlanFormData, UsageRate} from "../../../../plan";
import {InputGroup} from "primevue";
import {
  blankPlanFormDataValidationResult, convertInputSchemaToPlanFormData,
  convertPlanFormDataToInputSchema,
  PlanFormDataValidationResult,
  validatePlanFormData
} from "./services.ts";
import {
  Period,
} from "../../../../other/billing-cycle";
import {getAllCurrencies, getCurrencyByCode} from "../../../../other/currency";
import PeriodSelector from "../../../../core/components/period-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";
import UsageRateManager from "../../../../core/components/usage-rate-manager.vue";


interface P {
  initData?: PlanFormData,
}

const p = withDefaults(defineProps<P>(), {
  initData: () => ({
    title: "Hello World!",
    price: 110,
    currency: getCurrencyByCode("USD"),
    billingCycle: Period.enum.Monthly,
    description: "Test description",
    level: 1,
    features: "My first feature",
    usageRates: [],
    discounts: [],
    fields: {name: "Jack",},
  })
})

const e = defineEmits<{
  (e: "submit", data: PlanFormData): void,
  (e: "cancel"): void,
}>()


const inputSchema = ref(convertPlanFormDataToInputSchema(p.initData))
const validationResult: Ref<PlanFormDataValidationResult> = ref(blankPlanFormDataValidationResult())


// Usage Rate
const onAddUsageRate = () => {
  inputSchema.value.usageRates.push(
      {
        title: "",
        code: "",
        unit: "",
        availableUnits: 0,
        renewCycle: inputSchema.value.billingCycle,
      }
  )
}
const onDeleteUsageRate = (item: UsageRate) => {
  inputSchema.value.usageRates = inputSchema.value.usageRates.filter(x => x !== item)
}

// Discount
const createNewDiscount = () => {
  inputSchema.value.discounts.push({
    title: "",
    code: "",
    description: "",
    size: 0,
    validUntil: new Date(),
  })
}
const deleteDiscount = (value: Discount) => {
  inputSchema.value.discounts = inputSchema.value.discounts.filter(item => item.code != value.code)
}


const onSubmit = () => {
  validationResult.value = validatePlanFormData(inputSchema.value)
  if (validationResult.value.validated) {
    const data = convertInputSchemaToPlanFormData(inputSchema.value)
    e("submit", data)
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
                :options="getAllCurrencies()"
                optionLabel="name"
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


      <!--JsonFields text area-->
      <div class="w-full h-[10rem]">
        <IftaLabel class="h-full">
          <Textarea
              id="json_input"
              v-model="inputSchema.fields"
              style="resize: none;"
              class="w-full h-full"
              placeholder="Enter json data"
          />
          <label for="json_input">Fields</label>
        </IftaLabel>
        <Message severity="error" size="small" variant="simple" v-for="err in validationResult.fields" class="mt-1">
          {{ err }}
        </Message>
      </div>

      <!--UsageLimits-->
      <usage-rate-manager :usage-rates="inputSchema.usageRates"/>

      <!--Discounts-->
      <discount-manager :discounts="inputSchema.discounts"/>

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