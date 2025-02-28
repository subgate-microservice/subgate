<script setup lang="ts">
import {deleteAccount} from "../../../auth";
import {useConfirm} from "primevue/useconfirm";


const confirm = useConfirm();

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
    accept: deleteAccount,
    reject: () => {
    },
  });
};
</script>

<template>
  <div>
    <Panel header="Delete account" toggleable collapsed>
      <div class="flex flex-col gap-2">
        <div>
          Permanently deleting your account
        </div>
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