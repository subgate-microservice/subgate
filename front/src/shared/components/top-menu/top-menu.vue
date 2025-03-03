<script setup lang="ts">
import {useTopMenu} from "./store.ts";
import {useRouter} from "vue-router";
import {useAuthStore} from "../../../auth/myself.ts";

const store = useTopMenu()
const router = useRouter()
const auth = useAuthStore()

const onLogout = async () => {
  await auth.logout()
  await router.push({name: "Login"})
}

const onProfile = async () => {
  await router.push({name: "Profile"})
}
</script>

<template>
  <div class="flex justify-between w-full top-height top-font-size">
    <div>{{ store.headerTitle }}</div>
    <div class="flex gap-5">
      <i class="pi pi-user top-font-size cursor-pointer" @click="onProfile"/>
      <i class="pi pi-sign-out top-font-size cursor-pointer" @click="onLogout"/>
    </div>
  </div>
</template>

<style scoped>
@import "./styles.css";
</style>