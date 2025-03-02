<script setup lang="ts">
import {capitalize, ref} from "vue";
import {Period} from "../domain.ts";

const p = defineProps<{
  label: string
}>()

const allCycles = ref([
  Period.Daily,
  Period.Weekly,
  Period.Monthly,
  Period.Quarterly,
  Period.Semiannual,
  Period.Annual,
  Period.Lifetime,
])


const modelValue = defineModel({default: Period.Monthly})
</script>

<template>
  <IftaLabel>
    <Select
        v-model="modelValue"
        :options="allCycles"
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
    <label for="period">{{ p.label }}</label>
  </IftaLabel>
</template>

<style scoped>

</style>