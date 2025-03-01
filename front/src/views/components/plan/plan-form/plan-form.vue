<script setup lang="ts">
import {computed, ref, watch} from 'vue';
import {InputGroup} from "primevue";

import PeriodSelector from "../../../../core/components/period-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";
import UsageRateManager from "../../../../core/components/usage-rate-manager.vue";
import {recursive} from "../../../../utils/other.ts";
import {Period, PlanCreate} from "../../../../core/domain.ts";
import {z, ZodError} from "zod";


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
const valid = ref({discounts: true, simpleFields: true, usageRates: true})


const simpleFieldErrors = computed(() => {
  const validator = z.object({
    title: z.string(),
    price: z.number(),
    currency: z.string(),
    billingCycle: Period,
    description: z.string().nullable(),
    level: z.number(),
    features: z.string().nullable(),
  })

  const result: Record<string, string[]> = {
    title: [],
    price: [],
    currency: [],
    billingCycle: [],
    description: [],
    level: [],
    features: [],
  }

  try {
    validator.parse(inputSchema.value)
  } catch (err) {
    if (err instanceof ZodError) {
      for (let issue of err.errors) {
        const fieldName = issue.path[0]
        result[fieldName].push(fieldName + ": " + issue.message)
      }
    }
  }
  return result
})
watch(simpleFieldErrors, () => {
  valid.value.simpleFields = Object.keys(simpleFieldErrors.value).filter(v => v.length > 0).length === 0
})

const onSubmit = () => {
  const isValid = Object.values(valid.value).filter(v => !v).length === 0
  if (isValid) {
    console.log("Success")
  } else {
    console.log("validationError")
  }
}

const onCancel = () => {

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
          <Message severity="error" size="small" variant="simple" v-for="err in simpleFieldErrors.title" class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <IftaLabel>
          <InputNumber id="level" v-model="inputSchema.level" class="w-full"/>
          <label for="period">Level</label>
          <Message severity="error" size="small" variant="simple" v-for="err in simpleFieldErrors.level" class="mt-1">
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
              v-for="err in [...simpleFieldErrors.price, ...simpleFieldErrors.currency, ...simpleFieldErrors.billingCycle]"
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

      <usage-rate-manager :usage-rates="inputSchema.usageRates" v-model:validated="valid.usageRates"/>
      <discount-manager :discounts="inputSchema.discounts" v-model:validated="valid.discounts"/>

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