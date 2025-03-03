<script setup lang="ts">
import {Ref, ref} from "vue";
import {Panel} from "primevue";
import {EmailUpdate} from "../domain.ts";
import {useAuthStore} from "../myself.ts";

const mode: Ref<"change" | "verify"> = ref("change")

const store = useAuthStore()

const form: Ref<EmailUpdate> = ref({email: "test@test.com", password: "qwerty"})
const handleClickOnChange = async () => {
  await store.updateEmail(form.value)
  mode.value = "verify"
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