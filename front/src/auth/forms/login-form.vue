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
};
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
      </div>
    </template>
  </Card>
</template>