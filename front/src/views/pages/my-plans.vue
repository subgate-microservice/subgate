<script setup lang="ts">
import {ref, onMounted, Ref} from 'vue';
import {DataTable, Column, Drawer} from "primevue";
import {useTopMenu} from "../components/shared/top-menu";
import {ToolbarButtons} from "../components/shared/toolbar-menu";
import PlanForm from "../../core/forms/plan-form.vue";
import PlanInfo from "../../core/components/plan-info.vue";
import {findAndDelete, findAndReplace} from "../../utils/array-utils.ts";
import {getAmountString} from "../../other/currency";
import {ExpandedMenu} from "../components/shared/settings-menu";
import {Plan, PlanCreate, PlanUpdate} from "../../core/domain.ts";
import {PlanRepo} from "../../core/repositories.ts";
import {PlanMapper} from "../../core/mappers.ts";
import {useCreateDialogManager, useUpdateDialogManager} from "../../core/services.ts";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Plans"

const plans: Ref<Plan[]> = ref([])
const planRepo = new PlanRepo()
const planMapper = new PlanMapper()

const createDialog = useCreateDialogManager()
const updateDialog = useUpdateDialogManager<PlanUpdate>()
const infoDialog = useUpdateDialogManager<Plan>()


const saveCreatedPlan = async (data: PlanCreate) => {
  const created = await planRepo.create(data)
  plans.value = [...plans.value, created]
  createDialog.closeDialog()
}


const saveUpdatedPlan = async (data: PlanUpdate) => {
  const updated = await planRepo.update(data)
  findAndReplace(updated, plans.value, x => x.id)
  updateDialog.finishUpdate()
}

// Delete plan
const deleteOnePlan = async (item: Plan) => {
  await planRepo.deleteById(item.id)
  findAndDelete(item, plans.value, x => x.id)
}

const selectedPlans: Ref<Plan[]> = ref([])
const deleteSelected = async () => {
  const sby = {ids: selectedPlans.value.map(item => item.id)}
  await planRepo.deleteSelected(sby)
  const hashes = new Set(sby.ids)
  plans.value = plans.value.filter(item => !hashes.has(item.id))
  selectedPlans.value = []
}


onMounted(async () => {
  plans.value = await planRepo.getAll()
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
                @new="createDialog.openDialog()"
                @delete="deleteSelected"
                :disabled-delete="selectedPlans.length === 0"
                class="justify-end w-full"
            />
          </template>
          <template #body="slotProps">
            <expanded-menu
                @more="infoDialog.startUpdate(slotProps.data)"
                @edit="updateDialog.startUpdate(planMapper.toPlanUpdate(slotProps.data))"
                @delete="deleteOnePlan(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Drawer
        v-model:visible="infoDialog.state.showFlag"
        position="right"
        style="width: 60rem; max-width: 100vw"
    >
      <plan-info v-if="infoDialog.state.target" :item="infoDialog.state.target"/>
    </Drawer>

    <Dialog
        header="New plan"
        v-model:visible="createDialog.state.showFlag"
        modal
    >
      <plan-form @submit="saveCreatedPlan" @cancel="createDialog.closeDialog()"/>
    </Dialog>

    <Dialog header="Update plan" v-model:visible="updateDialog.state.showFlag" modal>
      <plan-form
          v-if="updateDialog.state.target"
          :init-data="updateDialog.state.target"
          @submit="saveUpdatedPlan"
          @cancel="updateDialog.finishUpdate()"
      />
    </Dialog>
  </div>
</template>


<style scoped>
.table-height {
  height: calc(100vh - 7rem);
}
</style>