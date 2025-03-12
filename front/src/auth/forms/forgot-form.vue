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
        <InputText name="login" placeholder="Enter email" v-model="formData.username" class="flex-1"/>
        <Button type="submit" severity="primary" label="Send" @click="onFormSubmit"/>
        <Button type="submit" severity="secondary" label="Back" @click="onBack"/>
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