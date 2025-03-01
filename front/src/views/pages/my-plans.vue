<script setup lang="ts">
import {ref, onMounted, Ref} from 'vue';
import {DataTable, Column, Drawer} from "primevue";
import {useTopMenu} from "../components/shared/top-menu";
import {ToolbarButtons} from "../components/shared/toolbar-menu";
import {
  deletePlanById, deleteSelectedPlans,
} from "../../plan";
import {PlanInfo} from "../components/plan/plan-info";
import PlanForm from "../../core/forms/plan-form.vue";
import {findAndDelete, findAndReplace} from "../../utils/array-utils.ts";
import {getAmountString} from "../../other/currency";
import {ExpandedMenu} from "../components/shared/settings-menu";
import {Plan, PlanCreate, PlanUpdate} from "../../core/domain.ts";
import {PlanService} from "../../core/services.ts";
import {PlanMapper} from "../../core/mappers.ts";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Plans"

const plans: Ref<Plan[]> = ref([])
const planService = new PlanService()
const planMapper = new PlanMapper()

// View plan info
const showPlanInfo = ref(false)
const planWithFullInfo: Ref<Plan | null> = ref(null);
const openFullInfo = (item: Plan) => {
  planWithFullInfo.value = item
  showPlanInfo.value = true
}


// Create plan
const showCreatePlanDialog = ref(false)
const startCreating = () => {
  showCreatePlanDialog.value = true
}
const cancelPlanCreating = () => {
  showCreatePlanDialog.value = false
}
const saveCreatedPlan = async (data: PlanCreate) => {
  const created = await planService.create(data)
  plans.value = [...plans.value, created]
  showCreatePlanDialog.value = false
}


// Update plan
const showUpdatePlanDialog = ref(false)
const planForUpdate: Ref<PlanUpdate | null> = ref(null)
const startPlanUpdating = (item: Plan) => {
  planForUpdate.value = planMapper.toPlanUpdate(item)
  showUpdatePlanDialog.value = true
}
const saveUpdatedPlan = async (data: PlanUpdate) => {
  await planService.update(data)
  findAndReplace(data, plans.value, x => x.id)
  planForUpdate.value = null
  showUpdatePlanDialog.value = false
}
const cancelUpdatePlan = () => {
  planForUpdate.value = null
  showUpdatePlanDialog.value = false
}

// Delete plan
const selectedPlans: Ref<Plan[]> = ref([])
const deleteOnePlan = async (item: Plan) => {
  await deletePlanById(item.id)
  findAndDelete(item, plans.value, x => x.id)
}
const deleteSelected = async () => {
  const sby = {ids: selectedPlans.value.map(item => item.id)}
  await deleteSelectedPlans(sby)
  const hashes = new Set(sby.ids)
  plans.value = plans.value.filter(item => !hashes.has(item.id))
  selectedPlans.value = []
}


onMounted(async () => {
  plans.value = await planService.getAll()
});


const COLUMN_STYLES = {
  table: {
    "max-with": "100%"
  },
  selectionCol: {
    "min-width": "3rem",
    "max-with": "3rem"
  },
  titleCol: {
    "min-width": "10rem",
    "max-width": "10rem",
    "white-space": "nowrap",
    "overflow": "hidden",
    "text-overflow": "ellipsis",
  },
  descriptionCol: {
    "min-width": "20rem",
    "max-width": "20rem",
    "white-space": "nowrap",
    "overflow": "hidden",
    "text-overflow": "ellipsis",
  },
  priceCol: {
    "min-width": "10rem",
    "max-width": "10rem",
  },
  billingCycleCol: {
    "min-width": "10rem",
    "max-width": "10rem",
  },
  levelCol: {
    "min-width": "10rem",
    "max-width": "10rem",
  },
  toolbarCol: {
    "min-width": "7rem",
    "max-with": "7rem"
  },
}
</script>

<template>
  <div class="w-full">
    <div class="card mt-2 table-height">
      <DataTable
          v-model:selection="selectedPlans"
          :value="plans"
          dataKey="id"
          scrollable
          scrollHeight="flex"
          size="small"
          :virtualScrollerOptions="{ itemSize: 46 }"
          style="width: 80rem; max-width: 100%"
      >
        <Column selectionMode="multiple" :style="COLUMN_STYLES.selectionCol"></Column>
        <Column field="title" header="Title" :style="COLUMN_STYLES.titleCol"></Column>
        <Column field="description" header="Description" :style="COLUMN_STYLES.descriptionCol"></Column>
        <Column field="" header="Price" :style="COLUMN_STYLES.priceCol">
          <template #body="slotProps">
            {{ getAmountString(slotProps.data.currency, slotProps.data.price) }}
          </template>
        </Column>
        <Column field="billingCycle" header="Billing cycle" :style="COLUMN_STYLES.billingCycleCol"></Column>
        <Column field="level" header="Level" :style="COLUMN_STYLES.levelCol"></Column>
        <Column :style="COLUMN_STYLES.toolbarCol">
          <template #header>
            <toolbar-buttons
                @new="startCreating"
                @delete="deleteSelected"
                :disabled-delete="selectedPlans.length === 0"
                class="justify-end w-full"
            />
          </template>
          <template #body="slotProps">
            <expanded-menu
                @more="openFullInfo(slotProps.data)"
                @edit="startPlanUpdating(slotProps.data)"
                @delete="deleteOnePlan(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Drawer v-model:visible="showPlanInfo" position="right" style="width: 60rem; max-width: 100vw">
      <plan-info v-if="planWithFullInfo" :item="planWithFullInfo"/>
    </Drawer>

    <Dialog header="New plan" v-model:visible="showCreatePlanDialog" modal>
      <plan-form @submit="saveCreatedPlan" @cancel="cancelPlanCreating"/>
    </Dialog>

    <Dialog header="Update plan" v-model:visible="showUpdatePlanDialog" modal>
      <plan-form
          v-if="planForUpdate"
          :init-data="planForUpdate"
          @submit="saveUpdatedPlan"
          @cancel="cancelUpdatePlan"
      />
    </Dialog>
  </div>
</template>


<style scoped>
.table-height {
  height: calc(100vh - 14rem);
}
</style>