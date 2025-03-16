<script setup lang="ts">
import {capitalize, ref, watch} from "vue";
import {SubscriptionStatus,} from "../../domain.ts";


const allStatuses = ref([SubscriptionStatus.Active, SubscriptionStatus.Paused, SubscriptionStatus.Expired])


const statusValue = defineModel("status", {default: SubscriptionStatus.Active})

const pausedFromValue = defineModel<Date | null>("pausedFrom", {default: null})

watch(statusValue, () => {
  if (statusValue.value === SubscriptionStatus.Paused) {
    if (!pausedFromValue.value)
      pausedFromValue.value = new Date()
  } else {
    pausedFromValue.value = null
  }
})

</script>

<template>
  <div>
    <IftaLabel>
      <Select
          id="StatusSelector"
          v-model="statusValue"
          :options="allStatuses"
          class="w-full"
      >
        <template #value="slotProps">
          <div v-if="slotProps.value" class="flex items-center">
            <div>{{ capitalize(slotProps.value) }}</div>
          </div>
          <span v-else>
            {{ slotProps.placeholder }}
        </span>
        </template>
        <template #option="slotProps">
          <div class="flex items-center">
            <div>{{ capitalize(slotProps.option) }}</div>
          </div>
        </template>
      </Select>
      <label for="StatusSelector">Status</label>
    </IftaLabel>


  </div>
</template>

<style scoped>

</style>