<script setup lang="ts">
import {Fieldset, DataTable, Column} from "primevue";
import {dateToString} from "../../shared/services/other.ts";
import {Plan} from "../domain.ts";
import {capitalize} from "vue";
import {CopyButton} from "../../shared/components/copy-button";
import {MyJson} from "../../shared/components/my-json";

const p = defineProps<{
  item: Plan,
}>()
</script>


<template>
  <div class="bg-surface-0 dark:bg-surface-950 p-5 md:p-10">
    <div class="bg-surface-0 dark:bg-surface-950">
      <div class="font-medium text-3xl text-surface-900 dark:text-surface-0 mb-4">Plan</div>
      <ul class="list-none p-0 m-0">
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">ID</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.item.id }}
          </div>
          <div class="w-6/12 md:w-2/12 flex justify-end">
            <copy-button :text-for-copy="p.item.id" message-after="ID copied"/>
          </div>
        </li>
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Title</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.item.title }}
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Description</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.item.description }}
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Price</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.item.price }} {{ p.item.currency }}
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Billing cycle</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ capitalize(p.item.billingCycle) }}
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Level</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.item.level }}
          </div>
        </li>


        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap"/>

      </ul>

      <div v-if="p.item.features.length" class="mt-4">
        <Fieldset legend="Features" :toggleable="true" :collapsed="true">
          <div>
            {{ p.item.features }}
          </div>
        </Fieldset>
      </div>

      <div v-if="p.item.usageRates.length" class="mt-4">
        <Fieldset legend="Usage rates" :toggleable="true" :collapsed="true">
          <DataTable :value="p.item.usageRates" class="mt-2">
            <Column field="title" header="Title"></Column>
            <Column field="code" header="Code"></Column>
            <Column field="unit" header="Unit"></Column>
            <Column field="availableUnits" header="Available units"></Column>
            <Column field="renewCycle" header="Renew cycle">
              <template #body="slotProps">
                {{ capitalize(slotProps.data.renewCycle) }}
              </template>
            </Column>
          </DataTable>
        </Fieldset>
      </div>

      <div v-if="p.item.discounts.length" class="mt-4">
        <Fieldset legend="Discounts" :toggleable="true" :collapsed="true" style="width: 100%">
          <DataTable :value="p.item.discounts">
            <Column field="title" header="Title"></Column>
            <Column field="code" header="Code"></Column>
            <Column field="description" header="Description"></Column>
            <Column field="size" header="Size">
              <template #body="slotProps">
                {{ slotProps.data.size }}%
              </template>
            </Column>
            <Column field="" header="Valid Until">
              <template #body="slotProps">
                {{ dateToString(slotProps.data.validUntil) }}
              </template>
            </Column>
          </DataTable>
        </Fieldset>
      </div>

      <div v-if="Object.keys(p.item.fields).length" class="mt-4">
        <Fieldset legend="Fields" :toggleable="true" :collapsed="true">
          <my-json :data="p.item.fields"/>
        </Fieldset>
      </div>
    </div>
  </div>
</template>

