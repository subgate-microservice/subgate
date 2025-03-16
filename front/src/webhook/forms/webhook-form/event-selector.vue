<script setup lang="ts">
import {EVENT_CODES} from "../../enums.ts";

const modelValue = defineModel<string | null>({default: null})
</script>

<template>
  <IftaLabel class="w-full">
    <Select
        id="eventSelector"
        class="w-full"
        :options="EVENT_CODES"
        placeholder="Select"
        v-model="modelValue"
    />
    <label for="eventSelector">Event code</label>
  </IftaLabel>
</template>

<style scoped>

</style>