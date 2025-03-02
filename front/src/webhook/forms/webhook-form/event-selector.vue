<script setup lang="ts">

</script>

<template>
  <IftaLabel class="w-full">
    <Select
        id="eventSelector"
        class="w-full"
        :options="['any_event']"
        optionLabel="name"
        placeholder="Event code"
    />
    <label for="eventSelector">Event code</label>
  </IftaLabel>
</template>

<style scoped>

</style>