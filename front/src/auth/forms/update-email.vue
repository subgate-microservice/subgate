<script setup lang="ts">
import {Ref, ref} from "vue";
import {Panel, useToast} from "primevue";
import {EmailUpdate} from "../domain.ts";
import {useAuthStore} from "../myself.ts";
import {useValidatorService} from "../../shared/services/validation-service.ts";
import {emailUpdateValidator} from "../validators.ts";

const mode: Ref<"change" | "verify"> = ref("change")

const store = useAuthStore()
const toast = useToast()

const form: Ref<EmailUpdate> = ref({email: "test@test.com", password: "qwerty"})

const validator = useValidatorService(form, emailUpdateValidator)

const handleClickOnChange = async () => {
  validator.validate()
  if (validator.isValidated) {
    try {
      await store.updateEmail(form.value)
      await store.logout()
    } catch (err: any) {
      console.error(err)
      const msg = err.message === "Request failed with status code 400"
          ? "Invalid old password"
          : String(err)
      toast.add({severity: "error", summary: msg, life: 3_000})
    }
  }
}

const verificationCode = ref("")
const handleClickOnVerify = async () => {
  await store.verifyEmail(verificationCode.value)
  await store.logout()
}


</script>
<template>
  <Panel toggleable collapsed>

    <template #header>
      <div>
        <div class="font-bold">Update email</div>
      </div>
    </template>

    <div v-if="mode === 'change'">
      <div class="flex flex-col gap-2">
        <InputText
            class="w-full"
            placeholder="New email"
            v-model="form.email"
        />
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('email')"
        >
          {{ err }}
        </Message>
        <InputText
            class="w-full"
            placeholder="Password"
            type="password"
            v-model="form.password"
        />
        <Button
            @click="handleClickOnChange"
            label="Change"
            class="w-max"
        />
      </div>
    </div>

    <div v-else-if="mode === 'verify'">
      <InputText
          placeholder="Verification code"
          v-model="verificationCode"
      />
      <Button
          class="ml-2"
          @click="handleClickOnVerify"
          label="Verify"
      />
    </div>
  </Panel>

</template>

<style scoped>

</style>