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
import {v4 as uuidv4} from "uuid";
import {
  BillingCycleCode,
  getAllBillingCycles,
  getBillingCycleByCode
} from "../../../../other/billing-cycle";
import {getAllCurrencies, getCurrencyByCode} from "../../../../other/currency";


interface P {
  initData?: PlanFormData,
}

const p = withDefaults(defineProps<P>(), {
  initData: () => ({
    title: "Hello World!",
    price: 110,
    currency: getCurrencyByCode("USD"),
    billingCycle: getBillingCycleByCode(BillingCycleCode.enum.Monthly),
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

const allCycles = getAllBillingCycles()

// Usage Rate
const onAddUsageRate = () => {
  inputSchema.value.usageRates.push(
      {availableUnits: 0, resource: "", unit: "", renewCycle: inputSchema.value.billingCycle}
  )
}
const onDeleteUsageRate = (item: UsageRate) => {
  inputSchema.value.usageRates = inputSchema.value.usageRates.filter(x => x !== item)
}

// Discount
const createNewDiscount = () => {
  inputSchema.value.discounts.push({
    id: uuidv4(),
    description: "",
    size: 0,
    validUntil: new Date(),
  })
}
const deleteDiscount = (value: Discount) => {
  inputSchema.value.discounts = inputSchema.value.discounts.filter(item => item.id != value.id)
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
          <IftaLabel class="w-2/4">
            <Select
                id="period"
                v-model="inputSchema.billingCycle"
                :options="allCycles"
                optionLabel="title"
            />
            <label for="period">Billing cycle</label>
          </IftaLabel>
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
      <div class="w-full mt-4">
        <div class="flex gap-2">
          <h2>Usage limits</h2>
          <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="onAddUsageRate"/>
        </div>

        <div v-if="inputSchema.usageRates.length === 0" class="mt-1">
          There are no usage rate parameters
        </div>

        <div v-for="item in inputSchema.usageRates">
          <InputGroup class="mt-2">
            <IftaLabel class="flex-grow">
              <InputText id="resource" v-model="item.resource" class="w-full"/>
              <label for="resource">Resource</label>
            </IftaLabel>
            <IftaLabel class="w-1/4">
              <InputText id="resource_unit" v-model="item.unit" class="w-full"/>
              <label for="resource_unit">Unit</label>
            </IftaLabel>
            <IftaLabel class="w-1/4">
              <InputNumber id="resource_limit" v-model="item.availableUnits" class="w-full"/>
              <label for="resource_limit">Limit</label>
            </IftaLabel>

            <IftaLabel>
              <Select
                  :id="'usagePeriod' + item.resource"
                  option-label="title"
                  v-model="item.renewCycle"
                  :options="allCycles"
                  class="w-full"
              />
              <label :for="'usagePeriod' + item.resource">Renew period</label>
            </IftaLabel>

            <Button
                icon="pi pi-trash"
                style="width: 5rem;"
                severity="contrast"
                @click="() => onDeleteUsageRate(item)"
            />
          </InputGroup>
          <Message
              severity="error" size="small" variant="simple" class="mt-1"
              v-for="err in validationResult.usageRates[item.resource]"
          >
            {{ err }}
          </Message>
        </div>
      </div>

      <!--Discounts-->
      <div class="w-full mt-4">
        <div class="flex gap-2">
          <h2>Discounts</h2>
          <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="createNewDiscount"/>
        </div>

        <div v-if="inputSchema.discounts.length === 0" class="mt-1">
          There are no discounts
        </div>

        <div v-for="item in inputSchema.discounts" :key="item.id">
          <InputGroup class="mt-2">
            <IftaLabel>
              <InputText :id="'Desc' + item.id" v-model="item.description" class="w-full"/>
              <label :for="'Desc' + item.id">Description</label>
            </IftaLabel>
            <IftaLabel>
              <InputNumber :id="'Amount' + item.id" v-model="item.size" class="w-full" suffix="%"/>
              <label :for="'Amount' + item.id">Size</label>
            </IftaLabel>
            <IftaLabel>
              <DatePicker :id="'ValidUntil' + item.id" v-model="item.validUntil" class="w-full"/>
              <label :for="'ValidUntil' + item.id">Expiration date</label>
            </IftaLabel>
            <Button
                icon="pi pi-trash"
                style="min-width: 1.25rem;"
                severity="contrast"
                @click="deleteDiscount(item)"
            />
          </InputGroup>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.discounts[item.id]"
                   class="mt-1">
            {{ err }}
          </Message>
        </div>

      </div>

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