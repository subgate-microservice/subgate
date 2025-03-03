<script setup lang="ts">

import {menuItems} from "./menu-items.ts";
import {Menu} from "primevue";
</script>

<template>
  <Menu
      :model="menuItems"
      class="sidebar-menu"
      style="border: none; background: var(--my-background);"
  >

  </Menu>
</template>

<style scoped>

</style>