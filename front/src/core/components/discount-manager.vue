<script setup lang="ts">
import {InputGroup} from "primevue";
import {Discount} from "../domain.ts";
import {computed, watch} from "vue";
import {z} from "zod";
import {fromError} from "zod-validation-error";

interface P {
  discounts?: Discount[]
}

const p = withDefaults(defineProps<P>(), {
  discounts: () => [],
})

const addDiscount = () => {
  p.discounts.push({
    title: "",
    code: "",
    size: 0,
    validUntil: new Date(),
  })
}

const removeDiscount = (value: Discount) => {
  p.discounts.splice(p.discounts.indexOf(value), 1)
}

const validated = defineModel("validated", {default: true})

const validationErrors = computed(() => {
  const result: Record<any, any> = {}

  const validator = z.object({
    title: z.string().min(2),
    code: z.string().min(2),
    description: z.string().optional(),
    size: z.number(),
    validUntil: z.date(),
  })

  for (let discount of p.discounts) {
    try {
      validator.parse(discount)
    } catch (err) {
      const discountValidationError = fromError(err)
      result[discount.code] = discountValidationError
          .toString()
          .split("Validation error: ")[1]
          .split(";")
    }
  }
  return result
})

watch(validationErrors, () => validated.value = Object.keys(validationErrors.value).length <= 0)

</script>

<template>
  <div class="w-full">
    <div class="flex gap-2">
      <h2>Discounts</h2>
      <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="addDiscount"/>
    </div>

    <div v-if="p.discounts.length === 0" class="mt-1">
      There are no discounts
    </div>

    <div v-for="item in p.discounts" :key="item.code">
      <InputGroup class="mt-2">

        <IftaLabel>
          <InputText :id="'Title' + item.code" v-model.lazy="item.title" class="w-full"/>
          <label :for="'Title' + item.code">Title</label>
        </IftaLabel>

        <IftaLabel>
          <InputText :id="'Code' + item.code" v-model.lazy="item.code" class="w-full"/>
          <label :for="'Code' + item.code">Code</label>
        </IftaLabel>

        <IftaLabel>
          <InputText :id="'Desc' + item.code" v-model.lazy="item.description" class="w-full"/>
          <label :for="'Desc' + item.code">Description</label>
        </IftaLabel>

        <IftaLabel>
          <InputNumber :id="'Amount' + item.code" v-model.lazy="item.size" class="w-full" suffix="%"/>
          <label :for="'Amount' + item.code">Size</label>
        </IftaLabel>

        <IftaLabel>
          <DatePicker :id="'ValidUntil' + item.code" v-model="item.validUntil" class="w-full"/>
          <label :for="'ValidUntil' + item.code">Expiration date</label>
        </IftaLabel>

        <Button
            icon="pi pi-trash"
            style="min-width: 1.25rem;"
            severity="contrast"
            @click="removeDiscount(item)"
        />
      </InputGroup>
      <Message
          v-for="err in validationErrors[item.code]"
          severity="error"
          size="small"
          variant="simple"
          class="mt-1"
      >
        {{ err }}
      </Message>
    </div>

  </div>

</template>

<style scoped>

</style>