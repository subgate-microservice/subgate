<script setup lang="ts">
import {computed, ModelRef, watch} from "vue";
import {z} from "zod";
import {fromError} from "zod-validation-error";
import {InputGroup, InputText, InputNumber, Button, Message} from "primevue";
import PeriodSelector from "./period-selector.vue";
import {Period, UsageRate} from "../domain.ts";

interface Props {
  basePeriod: Period
  showErrors: boolean
}

const p = defineProps<Props>();
const validated = defineModel("validated", {default: true});
const usageRates: ModelRef<UsageRate[]> = defineModel("usageRates", {default: () => []})

const addRate = () => {
  usageRates.value.push({
    title: "",
    code: "",
    unit: "",
    availableUnits: 0,
    renewCycle: p.basePeriod,
  });
};

const removeRate = (item: UsageRate) => {
  usageRates.value = usageRates.value.filter(rate => rate.code !== item.code)
};

const validator = z.object({
  title: z.string().min(2, "Title must be at least 2 characters"),
  code: z.string().min(2, "Code must be at least 2 characters"),
  unit: z.string().min(2, "Unit must be at least 2 characters")
});

const validationErrors = computed(() => {
  return usageRates.value.map((rate) => {
    try {
      validator.parse(rate);
      return [];
    } catch (err) {
      return fromError(err)
          .toString()
          .split("Validation error: ")[1]
          .split(";");
    }
  });
});


watch(validationErrors, () => {
  validated.value = validationErrors.value.every((errors) => errors.length === 0);
});
</script>


<template>
  <div class="w-full mt-4">
    <div class="flex gap-2">
      <h2>Usage rates</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addRate"/>
    </div>

    <div v-if="usageRates.length === 0" class="mt-1">
      There are no usage rate parameters
    </div>

    <div v-for="(item, i) in usageRates">
      <InputGroup class="mt-2">

        <IftaLabel class="flex-grow">
          <InputText id="title" v-model="item.title" class="w-full"/>
          <label for="title">Title</label>
        </IftaLabel>


        <IftaLabel class="flex-grow">
          <InputText id="code" v-model="item.code" class="w-full"/>
          <label for="code">Code</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputText id="code_unit" v-model="item.unit" class="w-full"/>
          <label for="code_unit">Unit</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <InputNumber id="code_limit" v-model="item.availableUnits" class="w-full" :min="0"/>
          <label for="code_limit">Limit</label>
        </IftaLabel>

        <period-selector label="Renew period" class="w-full" v-model="item.renewCycle"/>


        <Button
            icon="pi pi-trash"
            style="width: 5rem;"
            severity="contrast"
            @click="() => removeRate(item)"
        />
      </InputGroup>
      <Message
          v-if="p.showErrors"
          v-for="err in validationErrors[i]"
          severity="error" size="small" class="mt-1"
      >
        {{ err }}
      </Message>
    </div>
  </div>
</template>

<style scoped></style>
