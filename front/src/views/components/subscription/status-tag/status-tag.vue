<script setup lang="ts">
import {SubscriptionStatus} from "../../../../subscription/domain.ts";
import {Tag} from "primevue"

interface P {
  status: SubscriptionStatus,
}

const p = defineProps<P>()

const getSeverity = (item: SubscriptionStatus) => {
  switch (item) {
    case SubscriptionStatus.enum.Active:
      return "success"
    case SubscriptionStatus.enum.Paused:
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