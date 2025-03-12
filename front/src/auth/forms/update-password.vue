<script setup lang="ts">
import {Ref, ref} from "vue";
import {Panel, useToast} from "primevue";
import {PasswordUpdate} from "../domain.ts";
import {useAuthStore} from "../myself.ts";
import {useValidatorService} from "../../shared/services/validation-service.ts";
import {passwordUpdateValidator} from "../validators.ts";
import {useRouter} from "vue-router";

const store = useAuthStore()
const toast = useToast()
const router = useRouter()

const newPasswordForm: Ref<PasswordUpdate> = ref({
  oldPassword: "",
  newPassword: "",
  repeatPassword: "",
})

const validator = useValidatorService(newPasswordForm, passwordUpdateValidator)

async function handleClickOnChange() {
  validator.validate()
  if (validator.isValidated) {
    try {
      await store.updatePassword(newPasswordForm.value)
      await store.logout()
      await router.push({name: "Login"})
    } catch (err: any) {
      console.error(err)
      const msg = err.message === "Request failed with status code 400"
          ? "Invalid old password"
          : String(err)
      toast.add({severity: "error", summary: msg, life: 3_000})
    }

  }
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
      <Message
          severity="error"
          v-for="err in validator.getFieldErrors('newPassword')"
      >
        {{ err }}
      </Message>
      <InputText
          class="w-full"
          type="password"
          placeholder="Repeat password"
          v-model="newPasswordForm.repeatPassword"
      />
      <Message
          severity="error"
          v-for="err in validator.getFieldErrors('repeatPassword')"
      >
        {{ err }}
      </Message>
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