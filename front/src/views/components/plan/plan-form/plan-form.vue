<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { InputGroup } from "primevue";
import PeriodSelector from "../../../../core/components/period-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";
import UsageRateManager from "../../../../core/components/usage-rate-manager.vue";
import { recursive } from "../../../../utils/other.ts";
import { Period, PlanCreate } from "../../../../core/domain.ts";
import { z, ZodError } from "zod";

interface Props {
  initData?: PlanCreate;
}

const props = defineProps<Props>();
const emit = defineEmits(["submit", "cancel"]);

const defaultData: PlanCreate = {
  title: "string",
  price: 100,
  currency: "USD",
  billingCycle: Period.enum.Monthly,
  description: "",
  level: 10,
  features: "",
  usageRates: [],
  fields: {},
  discounts: [],
};

const formData = ref(recursive(props.initData ?? defaultData));
const valid = ref({ discounts: true, simpleFields: true, usageRates: true });

const validator = z.object({
  title: z.string().min(2),
  price: z.number().positive(),
  currency: z.string(),
  billingCycle: Period,
  description: z.string().nullable(),
  level: z.number().positive(),
  features: z.string().nullable(),
});

const simpleFieldErrors = computed(() => {
  try {
    validator.parse(formData.value);
    return {};
  } catch (err) {
    return err instanceof ZodError
        ? Object.fromEntries(err.errors.map(e => [e.path[0], e.message]))
        : {};
  }
});

watch(simpleFieldErrors, () => {
  valid.value.simpleFields = Object.keys(simpleFieldErrors.value).length === 0;
});

const onSubmit = () => {
  if (Object.values(valid.value).every(Boolean)) emit("submit", formData.value);
};
</script>

<template>
  <div class="w-[50rem] h-full flex flex-wrap gap-4">
    <div class="flex flex-col gap-3 flex-1">
      <IftaLabel>
        <InputText v-model="formData.title" class="w-full" />
        <label>Title</label>
        <Message v-if="simpleFieldErrors.title" severity="error">{{ simpleFieldErrors.title }}</Message>
      </IftaLabel>

      <IftaLabel>
        <InputNumber v-model="formData.level" class="w-full" />
        <label>Level</label>
        <Message v-if="simpleFieldErrors.level" severity="error">{{ simpleFieldErrors.level }}</Message>
      </IftaLabel>

      <IftaLabel>
        <Textarea v-model="formData.description" class="w-full" rows="3" style="resize: none" />
        <label>Description</label>
      </IftaLabel>

      <InputGroup>
        <IftaLabel class="w-1/4">
          <InputNumber v-model="formData.price" :minFractionDigits="2" :maxFractionDigits="5" />
          <label>Price</label>
        </IftaLabel>

        <IftaLabel class="w-1/4">
          <Select v-model="formData.currency" :options="['USD', 'EUR']" placeholder="Currency" />
          <label>Currency</label>
        </IftaLabel>

        <PeriodSelector v-model="formData.billingCycle" class="w-2/4" label="Billing cycle" />
      </InputGroup>
      <Message v-if="simpleFieldErrors.price" severity="error">{{ simpleFieldErrors.price }}</Message>

    </div>

    <IftaLabel class="w-full h-[10rem]">
      <Textarea v-model="formData.features" class="w-full h-full" placeholder="Enter features, one per line" />
      <label>Features</label>
    </IftaLabel>

    <UsageRateManager v-model:validated="valid.usageRates" :usage-rates="formData.usageRates" />
    <DiscountManager v-model:validated="valid.discounts" :discounts="formData.discounts" />

    <div class="flex flex-wrap gap-2">
      <Button label="Submit" @click="onSubmit" />
      <Button label="Cancel" outlined @click="$emit('cancel')" />
    </div>
  </div>
</template>
