<script setup lang="ts">

import {InputGroup} from "primevue";
import PeriodSelector from "./period-selector.vue";
import {Period, UsageRate} from "../domain.ts";
import {computed, watch} from "vue";
import {z} from "zod";
import {fromError} from "zod-validation-error";

interface P {
  usageRates?: UsageRate[]
  basePeriod?: Period,
}

const p = withDefaults(defineProps<P>(), {
  usageRates: () => [],
  basePeriod: Period.enum.Monthly,
})

const addRate = () => {
  p.usageRates.push({
    title: "",
    code: "",
    unit: "",
    availableUnits: 0,
    renewCycle: p.basePeriod,
  })
}

const removeRate = (rate: UsageRate) => {
  p.usageRates.splice(p.usageRates.indexOf(rate), 1)
}

const validated = defineModel("validated", {default: true})


const validationErrors = computed(() => {
  const result: Record<any, any> = {}

  const validator = z.object({
    title: z.string().min(2),
    code: z.string().min(2),
  })

  for (let rate of p.usageRates) {
    try {
      validator.parse(rate)
    } catch (err) {
      const rateValidationError = fromError(err)
      result[rate.code] = rateValidationError
          .toString()
          .split("Validation error: ")[1]
          .split(";")
    }
  }
  return result
})
watch(validationErrors, () => validated.value = Object.keys(validationErrors.value).length <= 0)


</script>

<template>
  <div class="w-full mt-4">
    <div class="flex gap-2">
      <h2>Usage rates</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addRate"/>
    </div>

    <div v-if="p.usageRates.length === 0" class="mt-1">
      There are no usage rate parameters
    </div>

    <div v-for="item in p.usageRates">
      <InputGroup class="mt-2">

        <IftaLabel class="flex-grow">
          <InputText id="title" v-model="item.title" class="w-full"/>
          <label for="title">Title</label>
        </IftaLabel>


        <IftaLabel class="flex-grow">
          <InputText id="code" v-model="item.code" class="w-full"/>
          <label for="code">Code</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputText id="code_unit" v-model="item.unit" class="w-full"/>
          <label for="code_unit">Unit</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputNumber id="code_limit" v-model="item.availableUnits" class="w-full"/>
          <label for="code_limit">Limit</label>
        </IftaLabel>

        <period-selector label="Renew period" class="w-full" v-model="item.renewCycle"/>


        <Button
            icon="pi pi-trash"
            style="width: 5rem;"
            severity="contrast"
            @click="() => removeRate(item)"
        />
      </InputGroup>
      <Message
          severity="error" size="small" variant="simple" class="mt-1"
          v-for="err in validationErrors[item.code]"
      >
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped>

</style>