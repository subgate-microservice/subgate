<script setup lang="ts">
import SidebarLayout from "./views/components/shared/sidebar-layout/sidebar-layout.vue";
import SidebarMenu from "./views/components/shared/sidebar-menu/sidebar-menu.vue";
import {TopMenu, TopLogo} from "./views/components/shared/top-menu";
import {Toast} from "primevue";
</script>

<template>
  <div>
    <Toast />
    <sidebar-layout>
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
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  font-family: SansSerif, Arial, sans-serif;

}

</style>
