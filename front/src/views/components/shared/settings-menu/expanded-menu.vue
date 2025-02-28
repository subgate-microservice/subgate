<script setup lang="ts">
import {useConfirm} from "primevue/useconfirm";

interface P {
  showEdit?: boolean,
  showDelete?: boolean,
  showView?: boolean,
}

const p = withDefaults(defineProps<P>(), {
  showEdit: true,
  showDelete: true,
  showView: true,
})

const e = defineEmits<{
  (e: "edit"): void,
  (e: "delete"): void,
  (e: "more"): void,
}>()

const confirm = useConfirm()


const onEdit = () => {
  e("edit")
}

const onMore = () => {
  e("more")
}

const onDelete = () => {
  confirm.require({
    message: 'Do you want to delete this item?',
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
  <div class="flex ">
    <Button
        v-if="p.showView"
        label=""
        class="p-button-rounded p-button-text"
        icon="pi pi-expand"
        @click="onMore"
        severity="contrast"
        outlined
    />
    <Button
        v-if="p.showEdit"
        label=""
        class="p-button-rounded p-button-text"
        icon="pi pi-pencil"
        @click="onEdit"
        severity="contrast"
        outlined
    />
    <Button
        v-if="p.showDelete"
        label=""
        class="p-button-rounded p-button-text"
        icon="pi pi-trash"
        @click="onDelete"
        severity="contrast"
        outlined
    />
  </div>
</template>

<style scoped>

</style>