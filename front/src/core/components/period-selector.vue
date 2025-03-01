<script setup lang="ts">
import {ref} from "vue";
import {Period} from "../domain.ts";
import {v4} from "uuid";

const p = defineProps<{
  label: string
}>()

const allCycles = ref([
  Period.enum.daily,
  Period.enum.weekly,
  Period.enum.monthly,
  Period.enum.quarterly,
  Period.enum.semiannual,
  Period.enum.annual,
  Period.enum.lifetime,
])

const modelValue = defineModel({default: Period.enum.monthly})
</script>

<template>
  <IftaLabel>
    <Select
        :id="v4()"
        v-model="modelValue"
        :options="allCycles"
    />
    <label for="period">{{ p.label }}</label>
  </IftaLabel>
</template>

<style scoped>

</style>