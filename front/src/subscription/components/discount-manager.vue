<script setup lang="ts">
import {computed, ModelRef} from "vue";
import {InputGroup, InputText, InputNumber, Button, Message} from "primevue";
import {Discount} from "../domain.ts";
import {ValidationService} from "../../shared/services/validation-service.ts";
import {blankDiscount} from "../factories.ts";

interface Props {
  validator: ValidationService
  fieldPrefix: string
}

const p = defineProps<Props>();

const discountsModel: ModelRef<Discount[]> = defineModel("discounts", {default: () => []})

const addDiscount = () => {
  discountsModel.value.push(blankDiscount())
};

const removeDiscount = (item: Discount) => {
  discountsModel.value = discountsModel.value.filter(disc => disc.code !== item.code)
}

const errors = computed(() => {
  const result = []
  for (let i = 0; i < discountsModel.value.length; i++) {
    const discountErrors = [
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.title`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.code`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.size`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.validUntil`),
      ...p.validator.getFieldErrors(`${p.fieldPrefix}.${i}.description`),
    ]
    result.push(discountErrors)
  }
  return result
})
</script>

<template>
  <div class="w-full mt-4">
    <div class="flex gap-2">
      <h2>Discounts</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addDiscount"/>
    </div>

    <div v-if="discountsModel.length === 0" class="mt-1">
      There are no discounts
    </div>

    <div v-for="(item, i) in discountsModel">
      <InputGroup class="mt-2">
        <IftaLabel class="flex-grow">
          <InputText v-model="item.title" class="w-full"/>
          <label>Title</label>
        </IftaLabel>

        <IftaLabel class="flex-grow">
          <InputText v-model="item.code" class="w-full"/>
          <label>Code</label>
        </IftaLabel>

        <IftaLabel class="flex-grow">
          <InputText v-model="item.description" class="w-full"/>
          <label>Description</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputNumber v-model="item.size" class="w-full" suffix="%" :min="0"/>
          <label>Size</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <DatePicker v-model="item.validUntil" class="w-full"/>
          <label>Valid until</label>
        </IftaLabel>

        <Button icon="pi pi-trash" style="width: 5rem;" severity="contrast" @click="() => removeDiscount(item)"/>
      </InputGroup>

      <Message
          v-for="err in errors[i]"
          severity="error"
          size="small"
          class="mt-1"
      >
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped></style>
