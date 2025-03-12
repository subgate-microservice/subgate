<script setup lang="ts">
import {ref} from 'vue';
import {Password, InputText, useToast} from "primevue";
import {useRouter} from "vue-router";
import {useAuthStore} from "../myself.ts";
import {useValidatorService} from "../../shared/services/validation-service.ts";
import {registerDataValidator} from "../validators.ts";
import {RegisterData} from "../domain.ts";

const router = useRouter()
const toast = useToast()

const formData = ref<RegisterData>({
  email: "test@test.com",
  password: "qwerty",
  repeat: "qwerty",
});

const validator = useValidatorService(formData, registerDataValidator)


const onFormSubmit = async () => {
  validator.validate()
  if (validator.isValidated) {
    try {
      await useAuthStore().register(formData.value)
      await router.push({name: "Plans"})
    } catch (err: any) {
      console.error(err)
      const msg = err?.response?.data?.detail === "REGISTER_USER_ALREADY_EXISTS"
          ? "User with this email already exist"
          : String(err)
      toast.add({severity: "error", summary: msg, life: 3_000})
    }

  }
}

const onBack = async () => {
  await router.push({name: "Login"})
}
</script>


<template>
  <Card>
    <template #title>
      New profile
    </template>
    <template #content>
      <div class="flex flex-col gap-3">
        <InputText name="login" placeholder="Email" v-model="formData.email"/>
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('email')"
        >
          {{ err }}
        </Message>

        <Password name="password" placeholder="Password" :feedback="false" fluid v-model="formData.password"/>
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('password')"
        >
          {{ err }}
        </Message>

        <Password name="password" placeholder="Password" :feedback="false" fluid v-model="formData.repeat"/>
        <Message
            severity="error"
            v-for="err in validator.getFieldErrors('repeat')"
        >
          {{ err }}
        </Message>

        <Button type="submit" severity="primary" label="Register" @click="onFormSubmit"/>
        <div class="flex justify-between">
          <div/>
          <div class="my-btn" @click="onBack">
            Already have a profile?
          </div>
        </div>

      </div>
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