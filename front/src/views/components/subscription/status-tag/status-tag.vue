<script setup lang="ts">
import {Tag} from "primevue"
import {SubscriptionStatus} from "../../../../core/domain.ts";

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
  <Tag :value="p.status" :severity="getSeverity(p.status)"/>
</template>

<style scoped>

</style>