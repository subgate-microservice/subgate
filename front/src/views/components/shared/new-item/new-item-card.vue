<script setup lang="ts">
import { Button, Dialog } from "primevue";

interface P {
  text?: string;
  buttonText?: string;
  dialogHeaderText?: string;
}

const p = withDefaults(defineProps<P>(), {
  text: () => "Click the button to create a new item",
  buttonText: () => "New item",
  dialogHeaderText: () => "Create new item",
});

const showDialogWindow = defineModel("dialogWindow", {default: true})

const toggleVisible = () => {
  showDialogWindow.value = !showDialogWindow.value
};
</script>

<template>
  <div>
    <Button
        :label="p.buttonText"
        @click="toggleVisible"
        class="w-full h-full"
        severity="secondary"
    />
    <Dialog
        v-model:visible="showDialogWindow"
        modal
        :header="p.dialogHeaderText"
    >
      <slot></slot>
    </Dialog>
  </div>
</template>

<style scoped></style>
