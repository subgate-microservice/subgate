<script setup lang="ts">
import {Ref, ref} from "vue";
import {logout, updatePassword, UpdatePasswordForm} from "../../../auth";
import {Panel} from "primevue";


const newPasswordForm: Ref<UpdatePasswordForm> = ref({
  oldPassword: "",
  newPassword: "",
  repeatPassword: "",
})

async function handleClickOnChange() {
  await updatePassword(newPasswordForm.value)
  await logout()
}
</script>

<template>
  <Panel header="Update password" toggleable collapsed>
    <div class="flex flex-col gap-2">
      <InputText
          class="w-full"
          type="password"
          placeholder="Old password"
          v-model="newPasswordForm.oldPassword"
      />
      <InputText
          class="w-full"
          type="password"
          placeholder="New password"
          v-model="newPasswordForm.newPassword"
      />
      <InputText
          class="w-full"
          type="password"
          placeholder="Repeat password"
          v-model="newPasswordForm.repeatPassword"
      />
      <Button
          @click="handleClickOnChange"
          label="Change"
          class="w-max"
      />
    </div>
  </Panel>

</template>

<style scoped>

</style>