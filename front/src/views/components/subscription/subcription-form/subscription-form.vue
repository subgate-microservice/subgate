<script setup lang="ts">
import {computed, onMounted, ref, Ref, watch} from "vue";
import {
  SubscriptionFormData, SubscriptionStatus,
} from "../../../../subscription/domain.ts";
import {Discount, Plan} from "../../../../plan";
import {InputGroup} from "primevue";
import {v4 as uuidv4} from 'uuid';
import {
  addCustomPlanOrReplaceIfTheOneAlreadyExist,
  blankInputSchema,
  blankValidationResult,
  convertFormDataToInputSchema,
  convertInputSchemaToFormData, createDiscountObject,
  createUsageObject,
  getAllPeriods,
  getAllPlans,
  getAllStatuses,
  InputSchema,
  SelectionItem,
  UsageInputSchema,
  validateInputSchema,
  ValidationResult,
} from "./services.ts";
import {BillingCycle} from "../../../../other/billing-cycle";
import {recursive} from "../../../../utils/other.ts";


const e = defineEmits<{
  (e: "submit", data: SubscriptionFormData): void,
  (e: "cancel"): void,
}>()

interface P {
  initData?: SubscriptionFormData,
}


const p = withDefaults(defineProps<P>(), {})

const inputSchema: Ref<InputSchema> = ref(blankInputSchema())

const allPlans: Ref<SelectionItem<Plan>[]> = ref([])
const allStatuses: Ref<SelectionItem<SubscriptionStatus>[]> = ref([])
const allPeriods: Ref<SelectionItem<BillingCycle>[]> = ref([])

const usages: Ref<Record<string, UsageInputSchema[]>> = ref({})
const discounts: Ref<Record<string, Discount[]>> = ref({})

// Следим за статусом, чтобы настраивать pausedFrom
const status = computed(() => inputSchema.value.selectedStatus)
watch(status, () => {
  if (status.value.value === SubscriptionStatus.enum.Paused) {
    if (!inputSchema.value.pausedFrom) {
      inputSchema.value.pausedFrom = new Date()
    }
  } else {
    inputSchema.value.pausedFrom = null
  }
})


// Каждый раз при смене выбранного плана, мы автоматически подстраиваем BillingCycle для подписки
const selectedPlan = computed(() => inputSchema.value?.selectedPlan?.value)
const selectedPlanWatcher = () => {
  if (selectedPlan.value) {
    inputSchema.value.selectedBillingCycle = {
      title: selectedPlan.value.billingCycle.title,
      code: selectedPlan.value.billingCycle.code,
      value: selectedPlan.value.billingCycle
    }
  }
}


const validationResult: Ref<ValidationResult> = ref(blankValidationResult())

// Discounts
const createNewDiscount = () => {
  if (selectedPlan.value) {
    const usage = {
      id: uuidv4(),
      description: "",
      size: 0,
      validUntil: new Date(),
    }
    const key = selectedPlan.value.id
    discounts.value[key].push(usage)
  }
}
const deleteDiscount = (value: Discount) => {
  if (selectedPlan.value) {
    const key = selectedPlan.value.id
    discounts.value[key] = discounts.value[key].filter(item => item.id !== value.id)
  } else {
    throw Error("SelectedPlan is undefined")
  }
}

// Usages
const createNewUsage = () => {
  if (selectedPlan.value) {
    const usage = {
      unit: "GB",
      resource: "Database",
      availableUnits: 110,
      usedUnits: 0,
      renewCycle: {
        title: selectedPlan.value.billingCycle.title,
        code: selectedPlan.value.billingCycle.code,
        value: selectedPlan.value.billingCycle,
      }
    }
    const key = selectedPlan.value.id
    usages.value[key].push(usage)
  }

}
const deleteUsage = (resource: string) => {
  if (selectedPlan.value) {
    const key = selectedPlan.value.id
    usages.value[key] = usages.value[key].filter(item => item.resource !== resource)
  }
}

const onSubmit = () => {
  if (selectedPlan.value) {
    const key = selectedPlan.value.id
    inputSchema.value.usages = usages.value[key]
    inputSchema.value.discounts = discounts.value[key]

    validationResult.value = validateInputSchema(inputSchema.value)
    if (validationResult.value.validated) {
      const data = convertInputSchemaToFormData(inputSchema.value)
      e("submit", data)
    }
  }
};

const onCancel = () => {
  e("cancel")
}

onMounted(async () => {
  allPeriods.value = getAllPeriods()
  allStatuses.value = getAllStatuses()
  allPlans.value = await getAllPlans()

  const usageObject = createUsageObject(allPlans.value.map(x => x.value))
  const discountObject = createDiscountObject(allPlans.value.map(x => x.value))
  if (p.initData) {
    const schema = convertFormDataToInputSchema(p.initData)
    addCustomPlanOrReplaceIfTheOneAlreadyExist(allPlans.value, p.initData.plan)
    usageObject[schema.selectedPlan!.value.id] = recursive(schema.usages)
    discountObject[schema.selectedPlan!.value.id] = recursive(schema.discounts)
    usages.value = usageObject
    discounts.value = discountObject
    inputSchema.value = schema
  } else {
    usages.value = usageObject
    discounts.value = discountObject
    inputSchema.value.selectedPlan = allPlans.value[0]
    selectedPlanWatcher()
  }
  watch(selectedPlan, selectedPlanWatcher)
})

</script>

<template>
  <div class="w-[50rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">

      <div class="flex flex-col gap-3 flex-1 core-plan-info">
        <!--Subscriber ID-->
        <IftaLabel>
          <InputText id="subscriberId" v-model="inputSchema.subscriberId" class="w-full"/>
          <label for="subscriberId">Subscriber ID</label>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.subscriberId"
                   class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <!--Status-->
        <IftaLabel>
          <Select
              id="StatusSelector"
              option-label="title"
              v-model="inputSchema.selectedStatus"
              :options="allStatuses"
              class="w-full"
          />
          <label for="StatusSelector">Status</label>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.status" class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <!--Selected plan-->
        <IftaLabel>
          <Select
              id="PlanSelector"
              option-label="title"
              v-model="inputSchema.selectedPlan"
              :options="allPlans"
              class="w-full"
          />
          <label for="PlanSelector">Plan</label>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.planId" class="mt-1">
            {{ err }}
          </Message>
        </IftaLabel>

        <!--Expiration date-->
        <div>
          <InputGroup>
            <IftaLabel>
              <Select
                  id="SubBillingCycle"
                  option-label="title"
                  v-model="inputSchema.selectedBillingCycle"
                  :options="allPeriods"
                  class="w-full"
              />
              <label for="SubBillingCycle">Billing cycle</label>
            </IftaLabel>
          </InputGroup>
          <Message severity="error" size="small" variant="simple" v-for="err in validationResult.startDate"
                   class="mt-1">
            {{ err }}
          </Message>
        </div>

        <div>

          <!--Autorenew-->
          <div class="flex gap-1 align-middle">
            <Checkbox inputId="autorenew" binary v-model="inputSchema.autorenew"/>
            <label for="autorenew" class="cursor-pointer select-none"> Autorenew </label>
          </div>

        </div>

        <!--Discounts-->
        <div class="w-full mt-4" v-if="inputSchema.selectedPlan">
          <div class="flex gap-2">
            <h2>Discounts</h2>
            <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="createNewDiscount"/>
          </div>

          <div v-if="discounts[inputSchema.selectedPlan.value.id].length === 0" class="mt-1">
            There are no discounts
          </div>

          <div v-for="item in discounts[inputSchema.selectedPlan.value.id]" :key="item.id">
            <InputGroup class="mt-2">
              <IftaLabel>
                <InputText :id="'Desc' + item.id" v-model="item.description" class="w-full"/>
                <label :for="'Desc' + item.id">Description</label>
              </IftaLabel>
              <IftaLabel>
                <InputNumber :id="'Amount' + item.id" v-model="item.size" class="w-full" suffix="%"/>
                <label :for="'Amount' + item.id">Size</label>
              </IftaLabel>
              <IftaLabel>
                <DatePicker :id="'ValidUntil' + item.id" v-model="item.validUntil" class="w-full"/>
                <label :for="'ValidUntil' + item.id">Expiration date</label>
              </IftaLabel>
              <Button
                  icon="pi pi-trash"
                  style="min-width: 1.25rem;"
                  severity="contrast"
                  @click="deleteDiscount(item)"
              />
            </InputGroup>
            <Message severity="error" size="small" variant="simple" v-for="err in validationResult.discounts[item.id]"
                     class="mt-1">
              {{ err }}
            </Message>
          </div>

        </div>

        <!--Usages-->
        <div class="w-full mt-4" v-if="inputSchema.selectedPlan">
          <div class="flex gap-2">
            <h2>Usages</h2>
            <i class="pi pi-plus-circle h-fit self-center cursor-pointer" @click="createNewUsage"/>
          </div>

          <div v-if="usages[inputSchema.selectedPlan.value.id].length === 0" class="mt-1">
            There are no usages
          </div>

          <div v-for="item in usages[inputSchema.selectedPlan.value.id]" :key="item.resource">
            <InputGroup class="mt-2">
              <IftaLabel>
                <InputText :id="'Resource' + item.resource" v-model="item.resource" class="w-full"/>
                <label :for="'Resource' + item.resource">Resource</label>
              </IftaLabel>
              <IftaLabel>
                <InputText :id="'Unit' + item.resource" v-model="item.unit" class="w-full"/>
                <label :for="'Unit' + item.resource">Unit</label>
              </IftaLabel>
              <IftaLabel>
                <InputNumber :id="'availableUnits' + item.resource" v-model="item.availableUnits" class="w-full"/>
                <label :for="'availableUnits' + item.resource">Available units</label>
              </IftaLabel>
              <IftaLabel>
                <InputNumber :id="'usedUnits' + item.resource" v-model="item.usedUnits" class="w-full"/>
                <label :for="'usedUnits' + item.resource">Used units</label>
              </IftaLabel>
              <IftaLabel>
                <Select
                    :id="'usagePeriod' + item.resource"
                    option-label="title"
                    v-model="item.renewCycle"
                    :options="allPeriods"
                    class="w-full"
                />
                <label :for="'usagePeriod' + item.resource">Renew period</label>
              </IftaLabel>

              <Button
                  icon="pi pi-trash"
                  style="min-width: 1.25rem;"
                  severity="contrast"
                  @click="deleteUsage(item.resource)"
              />
            </InputGroup>
            <Message severity="error" size="small" variant="simple"
                     v-for="err in validationResult.usages[item.resource]"
                     class="mt-1">
              {{ err }}
            </Message>
          </div>
        </div>


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