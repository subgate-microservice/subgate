<script setup lang="ts">
import {useTopMenu} from "../components/shared/top-menu";
import {Divider} from "primevue";
import {DeleteAccount, UpdateEmail, UpdatePassword} from "../components/auth";

const topStore = useTopMenu()
topStore.headerTitle = "Account"
</script>

<template>
  <div class="flex flex-col gap-2 items-center">
    <update-email class="max-w-[48rem] w-[48rem]"/>
    <update-password class="max-w-[48rem] w-[48rem]"/>

    <div class="mt-12 max-w-[48rem] w-[48rem]">
      <Divider align="left" type="solid">
        <b class="text-red-400">Danger zone</b>
      </Divider>
    </div>

    <delete-account class="max-w-[48rem] w-[48rem]"/>
  </div>
</template>

<style scoped>
</style>