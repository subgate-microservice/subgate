<script setup lang="ts">
import {Tag} from "primevue"
import {SubscriptionStatus} from "../domain.ts";
import {capitalize} from "vue";

interface P {
  status: SubscriptionStatus,
}

const p = defineProps<P>()

const getSeverity = (item: SubscriptionStatus) => {
  switch (item) {
    case SubscriptionStatus.Active:
      return "success"
    case SubscriptionStatus.Paused:
      return "warn"
    default:
      throw Error(`SwitchError ${item}`)
  }
}
</script>

<template>
  <Tag :value="capitalize(p.status)" :severity="getSeverity(p.status)"/>
</template>

<style scoped>

</style>