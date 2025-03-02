<script setup lang="ts">
import EventSelector from "./event-selector.vue";
import {computed, Ref, ref, watch} from "vue";
import {recursive} from "../../../utils/other.ts";
import {WebhookCU} from "../../domain.ts";
import {blankWebhookCU} from "../../factories.ts";
import {ZodError} from "zod";
import {webhookCUValidator} from "../../validators.ts";

const p = defineProps<{
  webhookCU?: WebhookCU,
}>()

const e = defineEmits(["submit", "cancel"])

const formData: Ref<WebhookCU> = ref(recursive(p.initData) ?? blankWebhookCU())

const valid = ref({simpleFields: true})
const showValidationErrors = ref(false)

const simpleFieldErrors = computed(() => {
  try {
    webhookCUValidator.parse(formData.value);
    return {};
  } catch (err) {
    return err instanceof ZodError
        ? Object.fromEntries(err.errors.map(e => [e.path[0], e.message]))
        : {};
  }
});

watch(simpleFieldErrors, () => {
  valid.value.simpleFields = Object.keys(simpleFieldErrors.value).length === 0;
}, {immediate: true});

const onSubmit = () => {
  const isValidated = Object.values(valid.value).every(v => v)
  if (isValidated) {
    e("submit", formData.value)
    showValidationErrors.value = false
  } else {
    showValidationErrors.value = true
  }
}


const onCancel = async () => {
  e("cancel")
}
</script>

<template>
  <div class="w-[30rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">
      <div class="flex flex-col gap-3 flex-1">
        <div>
          <IftaLabel class="w-full">
            <InputText
                v-model="formData.targetUrl"
                class="w-full"
                id="urlInput"
            />
            <label for="urlInput">Url</label>
            <Message
                v-if="simpleFieldErrors.targetUrl && showValidationErrors"
                severity="error"
                class="mt-1"
            >
              {{ simpleFieldErrors.targetUrl }}
            </Message>
          </IftaLabel>
        </div>

        <div>
          <event-selector v-model="formData.eventCode"/>
          <Message
              v-if="simpleFieldErrors.eventCode && showValidationErrors"
              severity="error"
              class="mt-1"
          >
            {{ simpleFieldErrors.eventCode }}
          </Message>
        </div>

        <div class="flex flex-wrap gap-2 mt-2">
          <Button label="Submit" @click="onSubmit"/>
          <Button label="Cancel" outlined @click="onCancel"/>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>

</style>