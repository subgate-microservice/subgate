<script setup lang="ts">
import {capitalize, ref} from "vue";
import {Period} from "../domain.ts";

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