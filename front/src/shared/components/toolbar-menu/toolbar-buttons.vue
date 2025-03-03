<script setup lang="ts">
import {useConfirm} from "primevue/useconfirm";

const e = defineEmits<{
  (e: "new"): void,
  (e: "delete"): void,
}>()

interface P {
  disabledDelete?: boolean,
}

const p = withDefaults(defineProps<P>(), {
  disabledDelete: false,
})

const confirm = useConfirm()


const clickOnNewBtn = () => e("new")
const clickOnDeleteBtn = () => {
  confirm.require({
    message: 'Do you want to delete this items?',
    header: 'Danger Zone',
    icon: 'pi pi-info-circle',
    rejectLabel: 'Cancel',
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Delete',
      severity: 'danger'
    },
    accept: () => {
      e("delete")
    },
    reject: () => {
    }
  });
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <Button
        label="New"
        icon="pi pi-plus"
        @click="clickOnNewBtn"
        size="small"
        severity="contrast"
    />
    <Button
        label="Delete"
        icon="pi pi-trash"
        @click="clickOnDeleteBtn"
        severity="danger"
        size="small"
        :disabled="p.disabledDelete"
        outlined
    />
  </div>
</template>

<style scoped>

</style>