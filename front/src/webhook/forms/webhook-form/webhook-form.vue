<script setup lang="ts">
import EventSelector from "./event-selector.vue";
import {Ref, ref} from "vue";
import {recursive} from "../../../shared/services/other.ts";
import {WebhookCU} from "../../domain.ts";
import {blankWebhookCU} from "../../factories.ts";
import {useValidatorService} from "../../../shared/services/validation-service.ts";
import {webhookCUValidator} from "../../validators.ts";

const p = defineProps<{
  webhookCU?: WebhookCU,
}>()

const e = defineEmits(["submit", "cancel"])

const formData: Ref<WebhookCU> = ref(recursive(p.webhookCU) ?? blankWebhookCU())

const validator = useValidatorService(formData, webhookCUValidator)


const onSubmit = () => {
  validator.validate()
  if (validator.isValidated) {
    e("submit", formData.value)
  } else {
    console.warn(validator.getAllErrors())
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
                v-for="msg in validator.getFieldErrors('targetUrl')"
                severity="error"
                class="mt-1"
            >
              {{ msg }}
            </Message>
          </IftaLabel>
        </div>

        <div>
          <event-selector v-model="formData.eventCode"/>
          <Message
              v-for="msg in validator.getFieldErrors('eventCode')"
              severity="error"
              class="mt-1"
          >
            {{ msg }}
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
