<script setup lang="ts">

import {InputGroup} from "primevue";
import PeriodSelector from "../../components/period-selector.vue";
import {Period} from "../../domain.ts";

const priceValue = defineModel("price", {default: 0})
const currencyValue = defineModel("currency", {default: "USD"})
const billingCycleValue = defineModel("billingCycle", {default: Period.enum.monthly})
</script>

<template>
  <div class="flex flex-col gap-3 flex-1">
    <InputGroup>
      <IftaLabel class="w-1/4">
        <InputNumber v-model="priceValue" :minFractionDigits="2" :maxFractionDigits="5"/>
        <label>Price</label>
      </IftaLabel>

      <IftaLabel class="w-1/4">
        <Select v-model="currencyValue" :options="['USD', 'EUR']" placeholder="Currency"/>
        <label>Currency</label>
      </IftaLabel>

      <PeriodSelector v-model="billingCycleValue" class="w-2/4" label="Billing cycle"/>
    </InputGroup>

  </div>

</template>

<style scoped>

</style>