<script setup lang="ts">

import {InputGroup} from "primevue";
import PeriodSelector from "./period-selector.vue";
import {Period, UsageRate} from "../domain.ts";

interface P {
  usageRates?: UsageRate[]
  basePeriod?: Period,
  validationErrors?: Record<string, string[]>
}

const p = withDefaults(defineProps<P>(), {
  usageRates: () => [],
  basePeriod: Period.enum.Monthly,
  validationErrors: () => ({}),
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
          v-for="err in p.validationErrors[item.code]"
      >
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped>

</style>