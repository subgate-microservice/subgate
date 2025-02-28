<script setup lang="ts">
import {Ref, ref} from "vue";
import {Apikey, ApikeyFormData, createApikey} from "../../../../auth";
import {CopyButton} from "../../shared/copy-button";
import {validateApikeyFormData, ValidationResults} from "./services.ts";

const e = defineEmits<{
  (e: "apikeyCreated", item: Apikey): void,
}>()

// Apikey value once showing
const showApikeyValueDialog = ref(false)
const apikeyValue: Ref<string | null> = ref(null)

const onCloseApikeyValueDialog = () => showApikeyValueDialog.value = false

// New apikey
const formData: Ref<ApikeyFormData> = ref({
  title: "",
})
const showApikeyFormDialog = ref(false)
const validationResults: Ref<ValidationResults> = ref({title: [], validated: true})


const startCreating = () => {
  showApikeyFormDialog.value = true
}

const submitForm = async () => {
  validationResults.value = validateApikeyFormData(formData.value)
  if (validationResults.value.validated) {
    const [apikey, value] = await createApikey(formData.value)
    apikeyValue.value = value
    showApikeyFormDialog.value = false
    showApikeyValueDialog.value = true
    formData.value = {title: ""}
    e("apikeyCreated", apikey)
  }
}

</script>
<template>
  <div>

    <Button
        label="New"
        icon="pi pi-plus-circle"
        class="w-max mt-2"
        @click="startCreating"
    />

    <Dialog v-model:visible="showApikeyValueDialog" modal header="API Key" class="max-w-[30rem]"
            @close="onCloseApikeyValueDialog">
      <div>
        Please save this value because we show it once. If you forget it you will need to generate new one.
      </div>
      <Message class="mt-6">
        <template #container>
          <div class="flex justify-between items-center pl-3">
            <div class="h-max">
              {{ apikeyValue }}
            </div>
            <copy-button
                :text-for-copy="apikeyValue!"
                message-after="API Key was copied"
            />
          </div>
        </template>
      </Message>
    </Dialog>

    <Dialog
        v-model:visible="showApikeyFormDialog"
        modal header="New API key" class="max-w-[30rem]"
    >
      <div class="flex flex-wrap gap-2">
        <InputText
            v-model="formData.title"
            placeholder="Title"
        />
        <Button
            label="Submit"
            @click="submitForm"
        />
      </div>
      <Message severity="error" size="small" variant="simple" v-for="err in validationResults.title" class="mt-1">
        {{ err }}
      </Message>
    </Dialog>
  </div>

</template>

<style scoped>

</style>