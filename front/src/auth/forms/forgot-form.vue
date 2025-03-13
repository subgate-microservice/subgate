<script setup lang="ts">
import {ref} from 'vue';
import {InputText, useToast} from "primevue";
import {useRouter} from "vue-router";
import {useValidatorService} from "../../shared/services/validation-service.ts";
import {emailValidator} from "../validators.ts";
import {useAuthStore} from "../myself.ts";

const router = useRouter()
const toast = useToast()

const form = ref({email: ""})
const validator = useValidatorService(form, emailValidator)

const onFormSubmit = async () => {
  try {
    validator.validate()
    if (validator.isValidated) {
      const store = useAuthStore()
      await store.forgotPassword(form.value.email)
      const msg = "We send reset link on email (not, really)"
      toast.add({severity: "success", summary: msg, life: 3_000})
    }
  } catch (err: any) {
    console.error(err)
    const msg = err?.message === "Request failed with status code 400"
        ? "Invalid email or password"
        : String(err)
    toast.add({severity: "error", summary: msg, life: 3_000})
  }
}

const onBack = async () => {
  await router.push({name: "Login"})
}


</script>


<template>
  <Card>
    <template #title>
      Forgot password
    </template>
    <template #content>
      <div class="flex gap-2">
        <InputText name="login" placeholder="Enter email" v-model="form.email" class="flex-1"/>
        <Button type="submit" severity="primary" label="Send" @click="onFormSubmit"/>
        <Button type="submit" severity="secondary" label="Back" @click="onBack"/>
      </div>
      <Message
          class="mt-1"
          severity="error"
          v-for="err in validator.getFieldErrors('email')"
      >
        {{ err }}
      </Message>
    </template>
  </Card>
</template>

<style scoped>
.my-btn {
  cursor: pointer;
}

.my-btn:hover {
  text-decoration: underline;
}
</style>