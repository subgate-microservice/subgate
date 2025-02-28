<script setup lang="ts">
import {getDataFromAuthCallback} from "../../auth/fief.ts";
import {onMounted} from "vue";

onMounted(async () => {
  await getDataFromAuthCallback()
})
</script>

<template>
  <div>
    callback
  </div>
</template>

<style scoped>

</style>