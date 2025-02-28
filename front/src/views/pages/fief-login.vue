<script setup lang="ts">
import {onBeforeMount} from "vue";
import {goToFiefLoginPage} from "../../auth/fief.ts";

onBeforeMount(async () => {
  await goToFiefLoginPage()
})
</script>

<template>

</template>

<style scoped>

</style>