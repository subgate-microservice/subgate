<script setup lang="ts">
import {ref} from "vue";
import {CopyButton} from "../../shared/components/copy-button";
import {Apikey, ApikeyCU} from "../domain.ts";
import {blankApikeyCU} from "../factories.ts";
import {ApikeyRepo} from "../repositories.ts";
import {useValidatorService} from "../../shared/services/validation-service.ts";
import {apikeyCUValidator} from "../validators.ts";
import {useCreateDialogManager, useUpdateDialogManager} from "../../shared/services/dialog-manager.ts";

const e = defineEmits<{
  (e: "apikeyCreated", item: Apikey): void,
}>()


const createDialog = useCreateDialogManager()
const showDialog = useUpdateDialogManager<string>()

const formData = ref(blankApikeyCU())
const validator = useValidatorService<ApikeyCU>(formData, apikeyCUValidator)

const submitForm = async () => {
  validator.validate()
  if (validator.isValidated) {
    const [apikey, value] = await new ApikeyRepo().createOne(formData.value)
    createDialog.closeDialog()
    showDialog.startUpdate(value)

    formData.value = blankApikeyCU()
    e("apikeyCreated", apikey)
  } else {
    console.warn(validator.getAllErrors())
  }
}

</script>
<template>
  <div>

    <Button
        label="New"
        icon="pi pi-plus-circle"
        class="w-max mt-2"
        @click="createDialog.openDialog()"
    />

    <Dialog
        v-model:visible="showDialog.state.showFlag"
        modal header="API Key"
        class="max-w-[30rem]"
        @close="showDialog.finishUpdate()"
    >
      <div>
        Please save this value because we show it once. If you forget it you will need to generate new one.
      </div>
      <Message class="mt-6">
        <template #container>
          <div class="flex justify-between items-center pl-3">
            <div class="h-max">
              {{ showDialog.state.target }}
            </div>
            <copy-button
                :text-for-copy="showDialog.state.target!"
                message-after="API Key was copied"
            />
          </div>
        </template>
      </Message>
    </Dialog>

    <Dialog
        v-model:visible="createDialog.state.showFlag"
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
      <Message
          v-for="err in validator.getAllErrors()"
          severity="error" size="small"
          class="mt-1"
      >
        {{ err }}
      </Message>
    </Dialog>
  </div>

</template>

<style scoped>

</style>