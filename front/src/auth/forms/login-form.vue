<script setup lang="ts">
import {ref} from 'vue';
import {Password, InputText, useToast} from "primevue";
import {useRouter} from "vue-router";
import {useAuthStore} from "../myself.ts";

const router = useRouter()
const toast = useToast()

const formData = ref({
  username: "test@test.com",
  password: "qwerty",
});


const onFormSubmit = async () => {
  try {
    await useAuthStore().login(formData.value)
    await router.push({name: "Plans"})
  } catch (err: any) {
    console.error(err)
    const msg = err?.message === "Request failed with status code 400"
        ? "Invalid email or password"
        : String(err)
    toast.add({severity: "error", summary: msg, life: 3_000})
  }
}

const onRegister = async () => {
  await router.push({name: "Register"})
}
</script>


<template>
  <Card>
    <template #title>
      Login
    </template>
    <template #content>
      <div class="flex flex-col gap-3">
        <InputText name="login" placeholder="Login" v-model="formData.username"/>
        <Password name="password" placeholder="Password" :feedback="false" fluid v-model="formData.password"/>
        <Button type="submit" severity="primary" label="Submit" @click="onFormSubmit"/>
        <Button type="submit" severity="secondary" label="Register" @click="onRegister"/>
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