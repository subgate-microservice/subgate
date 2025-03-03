<script setup lang="ts">
import {Toast} from "primevue";
import SidebarLayout from "./shared/components/sidebar-layout/sidebar-layout.vue";
import {TopLogo, TopMenu} from "./shared/components/top-menu";
import SidebarMenu from "./shared/components/sidebar-menu/sidebar-menu.vue";
import {useAuthStore} from "./auth/myself.ts";

const auth = useAuthStore()
</script>

<template>
  <div>
    <Toast/>
    <sidebar-layout v-if="auth.isAuthenticated">
      <template #logo>
        <top-logo class="pl-3"/>
      </template>
      <template #header>
        <top-menu/>
      </template>
      <template #sidebar>
        <sidebar-menu class=""/>
      </template>
      <template #content>
        <ConfirmDialog/>
        <router-view/>
      </template>
    </sidebar-layout>
    <div class="h-screen" v-else>
      <router-view/>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  font-family: SansSerif, Arial, sans-serif;
}

</style>
