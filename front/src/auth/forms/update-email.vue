<script setup lang="ts">
import {Ref, ref} from "vue";
import {logout, updateEmail, UpdateEmailForm, verifyEmail} from "../index.ts";
import {Panel} from "primevue";

const mode: Ref<"change" | "verify"> = ref("change")

const form: Ref<UpdateEmailForm> = ref({email: "barmatey6@gmail.com", password: "145190hfp"})
const handleClickOnChange = async () => {
  await updateEmail(form.value)
  mode.value = "verify"
}

const verificationCode = ref("")
const handleClickOnVerify = async () => {
  await verifyEmail(verificationCode.value)
  await logout()
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