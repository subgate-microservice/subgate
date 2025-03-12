<script setup lang="ts">
import {ref} from 'vue';
import {Password, InputText} from "primevue";
import {useRouter} from "vue-router";
import {useAuthStore} from "../myself.ts";

const router = useRouter()

const formData = ref({
  username: "test@test.com",
  password: "qwerty",
});


const onFormSubmit = async () => {
  await useAuthStore().login(formData.value)
  await router.push({name: "Plans"})
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
        <Button type="submit" severity="primary" label="Sign in" @click="onFormSubmit"/>
        <div class="flex justify-between">
          <div class="my-btn" @click="onRegister">
            Sign up
          </div>
          <div class="my-btn">
            Forgot password?
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