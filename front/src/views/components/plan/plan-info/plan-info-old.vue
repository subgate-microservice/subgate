<script setup lang="ts">
import {Plan} from "../../../../plan/domain.ts";
import {DataTable, Column, Fieldset} from "primevue";

interface P {
  plan: Plan,
}

const props = defineProps<P>()

</script>

<template>
  <div>
    <div class="flex flex-col gap-2">
      <div class="info-block ">
        <span class="text-gray-500 text-sm">Plan</span>
        <p class="text-xl font-semibold">{{ props.plan.title }} </p>
        <p class="">{{ props.plan.description }} </p>

      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div class="info-block">
          <span class="text-gray-500 text-sm">Price</span>
          <p class="text-xl font-semibold">{{ props.plan.price }} {{ props.plan.currency }}</p>
        </div>
        <div class="info-block">
          <span class="text-gray-500 text-sm">Period</span>
          <p class="text-xl font-semibold">{{ props.plan.billingCycle }}</p>
        </div>
        <div class="info-block">
          <span class="text-gray-500 text-sm">Level</span>
          <p class="text-xl font-semibold">{{ props.plan.level }}</p>
        </div>
      </div>
    </div>


    <div v-if="props.plan.features.length" class="mt-4">
      <Fieldset legend="Features" :toggleable="true" :collapsed="true">
        <div>
          {{ props.plan.features }}
        </div>
      </Fieldset>
    </div>

    <div v-if="props.plan.usageRates.length" class="mt-4">
      <Fieldset legend="Usage rates" :toggleable="true" :collapsed="true">
        <DataTable :value="props.plan.usageRates" class="mt-2">
          <Column field="resource" header="Resource"></Column>
          <Column field="unit" header="Unit"></Column>
          <Column field="pricePerUnit" header="Price Per Unit"></Column>
        </DataTable>
      </Fieldset>
    </div>

    <div v-if="Object.keys(props.plan.fields).length" class="mt-4">
      <Fieldset legend="Fields" :toggleable="true" :collapsed="true">
        <div class="text-gray-800">
          <pre style="background: white">{{ props.plan.fields }}</pre>
        </div>
      </Fieldset>
    </div>
  </div>
</template>

<style scoped>

.info-block {
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  text-align: center;
}

button {
  outline: none;
}

button i {
  font-size: 1.25rem;
}

ul {
  list-style-type: none;
  padding: 0;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background: #f3f4f6;
  padding: 1rem;
  border-radius: 0.5rem;
}

th, td {
  text-align: left;
}
</style>
