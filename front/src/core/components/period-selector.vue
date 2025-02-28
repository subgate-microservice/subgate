<script setup lang="ts">
import {ref} from "vue";
import {Period} from "../domain.ts";
import {v4} from "uuid";

const p = defineProps<{
  label: string
}>()

const allCycles = ref([
  Period.enum.Daily,
  Period.enum.Weekly,
  Period.enum.Monthly,
  Period.enum.Quarterly,
  Period.enum.Semiannual,
  Period.enum.Annual,
  Period.enum.Lifetime,
])

const modelValue = defineModel({default: Period.enum.Monthly})
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