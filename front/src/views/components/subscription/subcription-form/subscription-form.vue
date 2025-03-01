<script setup lang="ts">
import {onMounted, ref, Ref} from "vue";
import {recursive} from "../../../../utils/other.ts";
import {
  SubscriptionCreate,
  SubscriptionUpdate,
} from "../../../../core/domain.ts";
import {blankSubscriptionCreate} from "../../../../core/factories.ts";
import PlanSelector from "./plan-selector.vue";
import DiscountManager from "../../../../core/components/discount-manager.vue";


const e = defineEmits<{
  (e: "submit", data: SubscriptionCreate): void,
  (e: "cancel"): void,
}>()

const p = defineProps<{
  initData?: SubscriptionUpdate
}>()
const defaultValue = blankSubscriptionCreate()


const formData: Ref<SubscriptionCreate> = ref(recursive(p.initData) ?? defaultValue)

const validator = ref({discounts: true})


const onSubmit = () => {
  throw Error("NotImpl")
};

const onCancel = () => {
  e("cancel")
}

onMounted(async () => {

})

</script>

<template>
  <div class="w-[50rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">

      <div class="flex flex-col gap-3 flex-1 core-plan-info">
        <IftaLabel>
          <InputText id="subscriberId" v-model="formData.subscriberId" class="w-full"/>
          <label for="subscriberId">Subscriber ID</label>
        </IftaLabel>

        <!--Selected plan-->
        <plan-selector/>


        <div>
          <!--Autorenew-->
          <div class="flex gap-1 align-middle">
            <Checkbox inputId="autorenew" binary v-model="formData.autorenew"/>
            <label for="autorenew" class="cursor-pointer select-none"> Autorenew </label>
          </div>
        </div>

        <discount-manager :discounts="formData.discounts" v-model:validated="validator.discounts"/>

        <!--Navigate-->
        <div class="flex flex-wrap gap-2 mt-4">
          <Button
              label="Submit"
              @click="onSubmit"
          />
          <Button
              label="Cancel"
              @click="onCancel"
              outlined
          />
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>

</style>