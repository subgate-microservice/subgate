<script setup lang="ts">
import {useTopMenu} from "./store.ts";
import {logout} from "../../../../auth";

const store = useTopMenu()

const onLogout = async () => {
  await logout()
}
</script>

<template>
  <div class="flex justify-between w-full">
    <div class="text-2xl">
      {{ store.headerTitle }}
    </div>
    <Button label="logout" @click="onLogout"/>
  </div>
</template>

<style scoped>

</style>