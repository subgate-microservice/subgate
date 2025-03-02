<script setup lang="ts">
import {computed, ModelRef, watch} from "vue";
import {fromError} from "zod-validation-error";
import {InputGroup, InputText, InputNumber, Button, Message} from "primevue";
import {Discount} from "../domain.ts";
import {discountValidator} from "../validators.ts";

interface Props {
  showValidationErrors: boolean
}

const p = defineProps<Props>();
const validated = defineModel("validated", {default: true});
const discountsModel: ModelRef<Discount[]> = defineModel("discounts", {default: () => []})

const addDiscount = () => {
  discountsModel.value.push({
    title: "",
    code: "",
    size: 0,
    validUntil: new Date(),
    description: "",
  });
};

const removeDiscount = (item: Discount) => {
  discountsModel.value = discountsModel.value.filter(disc => disc.code !== item.code)
};

const validationErrors = computed(() =>
    discountsModel.value.map((discount) => {
      try {
        discountValidator.parse(discount);
        return [];
      } catch (err) {
        return fromError(err)
            .toString()
            .split("Validation error: ")[1]
            .split(";");
      }
    })
);

watch(validationErrors, () => {
  validated.value = validationErrors.value.every((errors) => errors.length === 0);
});
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
          <InputNumber v-model="item.size" class="w-full" suffix="%"/>
          <label>Size</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <DatePicker v-model="item.validUntil" class="w-full"/>
          <label>Valid until</label>
        </IftaLabel>

        <Button icon="pi pi-trash" style="width: 5rem;" severity="contrast" @click="() => removeDiscount(item)"/>
      </InputGroup>

      <Message
          v-if="p.showValidationErrors"
          v-for="err in validationErrors[i]"
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
