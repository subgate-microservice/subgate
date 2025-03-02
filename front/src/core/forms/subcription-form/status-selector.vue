<script setup lang="ts">
import {ModelRef, ref, watch} from "vue";
import {SubscriptionStatus,} from "../../domain.ts";


const allStatuses = ref([SubscriptionStatus.Active, SubscriptionStatus.Paused, SubscriptionStatus.Expired])


const statusValue = defineModel("status", {default: SubscriptionStatus.Active})

const pausedFromValue: ModelRef<Date | null> = defineModel("pausedFrom", {default: null})

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
      />
      <label for="StatusSelector">Status</label>
    </IftaLabel>


  </div>
</template>

<style scoped>

</style>