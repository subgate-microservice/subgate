<script setup lang="ts">
import {InputGroup} from "primevue";
import {Discount} from "../domain.ts";
import {ref, Ref} from "vue";

interface P {
  discounts: Discount[]
}

const p = withDefaults(defineProps<P>(), {
  discounts: () => [],
})

const validationErrors: Ref<Record<string, string[]>> = ref({})

const addDiscount = () => {
}

const removeDiscount = (value: Discount) => {
  p.discounts.splice(p.discounts.indexOf(value), 1)
}
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
          <InputText :id="'Desc' + item.code" v-model="item.description" class="w-full"/>
          <label :for="'Desc' + item.code">Description</label>
        </IftaLabel>
        <IftaLabel>
          <InputNumber :id="'Amount' + item.code" v-model="item.size" class="w-full" suffix="%"/>
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
      <Message severity="error" size="small" variant="simple" v-for="err in validationErrors[item.code]"
               class="mt-1">
        {{ err }}
      </Message>
    </div>

  </div>

</template>

<style scoped>

</style>