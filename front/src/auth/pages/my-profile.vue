<script setup lang="ts">
import {Divider} from "primevue";
import DeleteAccount from "../forms/delete-account.vue";
import UpdatePassword from "../forms/update-password.vue";
import UpdateEmail from "../forms/update-email.vue";
import {useTopMenu} from "../../shared/components/top-menu";

const topStore = useTopMenu()
topStore.headerTitle = "Profile"
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