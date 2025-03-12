<script setup lang="ts">
import {useConfirm} from "primevue/useconfirm";
import {useAuthStore} from "../myself.ts";
import {ref} from "vue";
import {useRouter} from "vue-router";
import {useToast} from "primevue";


const confirm = useConfirm();
const password = ref("")
const router = useRouter()
const toast = useToast()

async function deleteProfile() {
  try {
    const store = useAuthStore()
    await store.deleteAccount(password.value)
    await router.push({name: "Login"})
  } catch (err: any) {
    console.error(err)
    const msg = err.message === "Request failed with status code 400"
        ? "Invalid password"
        : String(err)
    toast.add({severity: "error", summary: msg, life: 3_000})
  }
}

const clickOnDelete = () => {
  confirm.require({
    message: 'Are you sure you want to proceed?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: 'No',
      severity: 'contrast',
    },
    acceptProps: {
      label: 'Yes',
      severity: 'contrast',
      outlined: true,
    },
    accept: deleteProfile,
    reject: () => {
    },
  });
};
</script>

<template>
  <div>
    <Panel header="Delete profile" toggleable collapsed>
      <div class="flex flex-col gap-2">
        <div>
          Permanently deleting your profile
        </div>
        <InputText
            v-model="password"
            type="password"
        />
        <Button
            @click="() => clickOnDelete()"
            label="Delete"
            class="w-max"
            outlined
            severity="danger"
        />
      </div>

    </Panel>
  </div>
</template>

<style scoped>

</style>