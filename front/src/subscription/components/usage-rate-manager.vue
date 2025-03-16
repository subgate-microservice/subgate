<script setup lang="ts">
import {computed} from "vue";
import {InputGroup, InputText, InputNumber, Button, Message} from "primevue";
import PeriodSelector from "./period-selector.vue";
import {Period, UsageRate} from "../domain.ts";
import {ValidationService} from "../../shared/services/validation-service.ts";
import {blankUsage, blankUsageRate} from "../factories.ts";

interface Props {
  basePeriod: Period
  validator: ValidationService
  fieldPrefix: string
  itemType: "usageRate" | "usage"
}

const p = defineProps<Props>()

const items = defineModel<UsageRate[]>("usageRates", {default: () => []})

const addItem = () => {
  const item = p.itemType === "usageRate"
      ? blankUsageRate()
      : blankUsage()
  items.value.push(item)
};

const removeItem = (item: UsageRate) => {
  items.value = items.value.filter(rate => rate.code !== item.code)
}

const errors = computed(() => {
  const result = []
  for (let i = 0; i < items.value.length; i++) {
    const usageRateErrors = [
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.title`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.code`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.unit`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.availableUnits`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.renewCycle`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.usedUnits`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.lastRenew`),
    ]
    result.push(usageRateErrors)
  }
  return result
})
</script>


<template>
  <div class="w-full mt-4">
    <div class="flex gap-2">
      <h2>Usage rates</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addItem"/>
    </div>

    <div v-if="items.length === 0" class="mt-1">
      There are no usage rate parameters
    </div>

    <div v-for="(item, i) in items">
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
          <InputNumber id="code_limit" v-model="item.availableUnits" class="w-full" :min="0"/>
          <label for="code_limit">Limit</label>
        </IftaLabel>

        <period-selector label="Renew period" class="w-full" v-model="item.renewCycle"/>

        <Button
            icon="pi pi-trash"
            style="width: 5rem;"
            severity="contrast"
            @click="() => removeItem(item)"
        />
      </InputGroup>
      <Message
          v-for="err in errors[i]"
          severity="error" size="small" class="mt-1"
      >
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped></style>
