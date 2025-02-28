<script setup lang="ts">
import {useTopMenu} from "./store.ts";
import {logout} from "../../../../auth";
import {useRouter} from "vue-router";

const store = useTopMenu()
const router = useRouter()

const onLogout = async () => {
  await logout()
  await router.push({name: "Login"})
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