<script setup lang="ts">
import {onMounted, ref, Ref} from "vue";

import {WebhookFormData} from "../../../../webhook";
import {
  blankValidationResult, convertInputSchemaToWebhookFormData,
  convertWebhookFormDataToInputSchema,
  EventCodeItem, validateInputSchema,
  ValidationResult
} from "./services.ts";
import {EventCode, getAllEventCodes} from "../../../../other/event-code";


const e = defineEmits<{
  (e: "submit", data: WebhookFormData): void,
  (e: "cancel"): void,
}>()

interface P {
  initData?: WebhookFormData,
}


const p = withDefaults(defineProps<P>(), {
  initData: () => ({
    eventCode: EventCode.enum.SubscriptionCreated,
    targetUrl: "",
  })
})

const inputSchema = ref(convertWebhookFormDataToInputSchema(p.initData))
const validationResult: Ref<ValidationResult> = ref(blankValidationResult())


const onSubmit = () => {
  validationResult.value = validateInputSchema(inputSchema.value)
  if (validationResult.value.validated) {
    const data = convertInputSchemaToWebhookFormData(inputSchema.value)
    e("submit", data)
  }
};

const onCancel = () => {
  e("cancel")
}

// Event codes
const eventCodes: Ref<EventCodeItem[]> = ref([])

onMounted(async () => {
  eventCodes.value = (await getAllEventCodes()).map(x => ({name: x, code: x, value: x}))
})


</script>

<template>
  <div class="w-[30rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">
      <div class="flex flex-col gap-3 flex-1">
        <div>
          <IftaLabel class="w-full">
            <InputText
                class="w-full"
                id="urlInput"
                v-model="inputSchema.targetUrl"
            />
            <label for="urlInput">Url</label>
          </IftaLabel>
          <Message
              severity="error" size="small" variant="simple" class="mt-1"
              v-for="err in validationResult.targetUrl"
          >
            {{ err }}
          </Message>
        </div>

        <IftaLabel class="w-full">
          <Select
              id="eventSelector"
              class="w-full"
              v-model="inputSchema.selectedEvent"
              :options="eventCodes"
              optionLabel="name"
              placeholder="Event code"
          />
          <label for="eventSelector">Event code</label>
        </IftaLabel>

        <div class="flex flex-wrap gap-2 mt-2">
          <Button
              label="Submit"
              @click="onSubmit"
          />
          <Button
              label="Cancel"
              outlined
              @click="onCancel"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>