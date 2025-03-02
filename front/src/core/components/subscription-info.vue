<script setup lang="ts">
import {Fieldset, DataTable, Column} from "primevue";
import {CopyButton} from "../../views/components/shared/copy-button";
import {dateToString} from "../../utils/other.ts";
import {Subscription} from "../domain.ts";
import StatusTag from "./status-tag.vue";
import {capitalize} from "vue";
import {getNextBilling} from "../services.ts";

const p = defineProps<{
  subscription: Subscription,
}>()
</script>


<template>
  <div class="bg-surface-0 dark:bg-surface-950 p-5 md:p-10">
    <div class="bg-surface-0 dark:bg-surface-950">
      <div class="font-medium text-3xl text-surface-900 dark:text-surface-0 mb-4">Subscription</div>
      <ul class="list-none p-0 m-0">
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">ID</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.subscription.id }}
          </div>
          <div class="w-6/12 md:w-2/12 flex justify-end">
            <copy-button :text-for-copy="p.subscription.id" message-after="ID copied"/>
          </div>
        </li>
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Subscriber ID</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.subscription.subscriberId }}
          </div>
          <div class="w-6/12 md:w-2/12 flex justify-end">
            <copy-button :text-for-copy="p.subscription.subscriberId" message-after="Subscriber ID copied"/>
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Status</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            <status-tag :status="p.subscription.status"/>
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Plan</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.subscription.planInfo.title }}
          </div>
        </li>

        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Billing cycle</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ capitalize(p.subscription.billingInfo.billingCycle) }}
          </div>
        </li>


        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Created</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ dateToString(p.subscription.createdAt) }}
          </div>
        </li>
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Last billing</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ dateToString(p.subscription.billingInfo.lastBilling) }}
          </div>
        </li>
        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap">
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Next billing</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ dateToString(getNextBilling(p.subscription)) }}
          </div>
        </li>

        <li
            v-if="p.subscription.billingInfo.savedDays > 0"
            class="flex items-center py-4 px-2 border-t border-surface flex-wrap"
        >
          <div class="text-surface-500 dark:text-surface-300 w-6/12 md:w-2/12 font-medium">Saved days</div>
          <div class="text-surface-900 dark:text-surface-0 w-full md:w-8/12 md:order-none order-1">
            {{ p.subscription.billingInfo.savedDays }}
          </div>
        </li>


        <li class="flex items-center py-4 px-2 border-t border-surface flex-wrap"/>

      </ul>

      <div v-if="p.subscription.discounts.length" class="mt-4">
        <Fieldset legend="Discounts" :toggleable="true" :collapsed="true" style="width: 100%">
          <DataTable :value="p.subscription.discounts">
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

      <div v-if="p.subscription.usages.length" class="mt-4">
        <Fieldset legend="Usages" :toggleable="true" :collapsed="true">
          <DataTable :value="p.subscription.usages">
            <Column field="resource" header="Resource"></Column>
            <Column field="availableUnits" header="Available units"></Column>
            <Column field="usedUnits" header="Used units"></Column>
            <Column field="renewCycle" header="Renew cycle">
              <template #body="slotProps">
                {{ slotProps.data.renewCycle.title }}
              </template>
            </Column>

          </DataTable>
        </Fieldset>
      </div>
    </div>
  </div>
</template>
