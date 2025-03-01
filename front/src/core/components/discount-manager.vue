<script setup lang="ts">
import { computed, watch } from "vue";
import { z } from "zod";
import { fromError } from "zod-validation-error";
import { InputGroup, InputText, InputNumber, Button, Message } from "primevue";
import { Discount } from "../domain.ts";

interface Props {
  discounts: Discount[];
}

const p = defineProps<Props>();
const validated = defineModel("validated", { default: true });

const addDiscount = () => {
  p.discounts.push({
    title: "",
    code: "",
    size: 0,
    validUntil: new Date(),
  });
};

const removeDiscount = (item: Discount) => {
  const index = p.discounts.indexOf(item);
  p.discounts.splice(index, 1);
};

const validator = z.object({
  title: z.string().min(2, "Title must be at least 2 characters"),
  code: z.string().min(2, "Code must be at least 2 characters"),
  description: z.string().optional(),
  size: z.number().min(0, "Size must be a positive number"),
  validUntil: z.date(),
});

const validationErrors = computed(() =>
    p.discounts.map((discount) => {
      try {
        validator.parse(discount);
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
  validated.value = validationErrors.value.every((err) => !err.length);
});
</script>

<template>
  <div class="w-full mt-4">
    <div class="flex gap-2">
      <h2>Discounts</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addDiscount" />
    </div>

    <div v-if="p.discounts.length === 0" class="mt-1">
      There are no discounts
    </div>

    <div v-for="(item, i) in p.discounts">
      <InputGroup class="mt-2">
        <IftaLabel class="flex-grow">
          <InputText v-model="item.title" class="w-full" />
          <label>Title</label>
        </IftaLabel>

        <IftaLabel class="flex-grow">
          <InputText v-model="item.code" class="w-full" />
          <label>Code</label>
        </IftaLabel>

        <IftaLabel class="flex-grow">
          <InputText v-model="item.description" class="w-full" />
          <label>Description</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputNumber v-model="item.size" class="w-full" suffix="%" />
          <label>Size</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <DatePicker v-model="item.validUntil" class="w-full" />
          <label>Valid until</label>
        </IftaLabel>

        <Button icon="pi pi-trash" style="width: 5rem;" severity="contrast" @click="() => removeDiscount(item)" />
      </InputGroup>

      <Message v-for="err in validationErrors[i]" severity="error" size="small" class="mt-1">
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped></style>
