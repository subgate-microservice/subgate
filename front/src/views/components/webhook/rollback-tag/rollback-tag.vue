<script setup lang="ts">
import {Tag} from "primevue"
import {computed} from "vue";

interface P {
  rollbackIfWebhookFailed: boolean,
}

const p = defineProps<P>()

const severity = computed(() => p.rollbackIfWebhookFailed ? "danger" : "success")
const value = computed(() => p.rollbackIfWebhookFailed ? "Rollback" : "Miss")

</script>

<template>
  <Tag :value="value" :severity="severity"/>
</template>

<style scoped>

</style>