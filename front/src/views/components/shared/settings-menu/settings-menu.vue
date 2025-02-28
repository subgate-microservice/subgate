<script setup lang="ts">
import {Menu} from "primevue";
import {ref} from "vue";
import {useConfirm} from "primevue/useconfirm";

const e = defineEmits<{
  (e: "edit"): void,
  (e: "delete"): void,
}>()

const menu = ref();

const confirm = useConfirm()

const menuToggle = (event: any) => {
  menu.value.toggle(event);
};


const showEditMode = ref(false)


const onDelete = () => {
  confirm.require({
    message: 'Do you want to delete this plan?',
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

const menuItems = [
  {
    items: [
      {
        label: 'Edit',
        icon: 'pi pi-refresh',
        command: () => showEditMode.value = true
      },
      {
        label: 'Delete',
        icon: 'pi pi-trash',
        command: onDelete
      }
    ]
  }
]
</script>

<template>
  <div>
    <Button
        class="p-button-rounded p-button-text"
        icon="pi pi-cog"
        @click="menuToggle"
        aria-haspopup="true"
        aria-controls="overlay_menu"
        severity="contrast"
    />
    <Menu ref="menu" id="overlay_menu" :model="menuItems" :popup="true"/>
  </div>
</template>

<style scoped>

</style>