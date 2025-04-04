<script setup lang="ts">
import {ref, onMounted, Ref, capitalize} from 'vue';
import {DataTable, Column, Drawer} from "primevue";
import {findAndDelete, findAndReplace} from "../../shared/services/array-utils.ts";
import {getNextBilling} from "../services.ts";
import {SubscriptionRepo} from "../repositories.ts";
import {Subscription, SubscriptionCU} from "../domain.ts";
import {SubscriptionMapper} from "../mappers.ts";
import {SubscriptionForm} from "../forms/subcription-form";
import {dateToString} from "../../shared/services/other.ts";
import StatusTag from "../components/status-tag.vue";
import SubscriptionInfo from "../components/subscription-info.vue";
import {useCreateDialogManager, useUpdateDialogManager} from "../../shared/services/dialog-manager.ts";
import {useTopMenu} from "../../shared/components/top-menu";
import {CopyWrapper} from "../../shared/components/copy-button";
import {ToolbarButtons} from "../../shared/components/toolbar-menu";
import {ExpandedMenu} from "../../shared/components/settings-menu";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Subscriptions"

const subRepo = new SubscriptionRepo()
const subMapper = new SubscriptionMapper()

const subscriptions: Ref<Subscription[]> = ref([])

const createDialog = useCreateDialogManager()
const updateDialog = useUpdateDialogManager<Subscription>()
const infoDialog = useUpdateDialogManager<Subscription>()


const saveCreated = async (item: SubscriptionCU) => {
  const created = await subRepo.create(item)
  subscriptions.value = [...subscriptions.value, created]
  createDialog.closeDialog()
}

const saveUpdated = async (item: SubscriptionCU) => {
  const updated = await subRepo.update(item)
  findAndReplace(updated, subscriptions.value, x => x.id)
  updateDialog.finishUpdate()
}


// Delete subscription
const selected: Ref<Subscription[]> = ref([]);
const deleteOne = async (item: Subscription) => {
  await subRepo.deleteById(item.id)
  findAndDelete(item, subscriptions.value, x => x.id)
}
const deleteSelected = async () => {
  const sby = {ids: selected.value.map(x => x.id)}
  await subRepo.deleteSelected(sby)

  const hashes = new Set(sby.ids)
  subscriptions.value = subscriptions.value.filter(x => !hashes.has(x.id))
  selected.value = []
}


onMounted(async () => {
  subscriptions.value = await subRepo.getSelected()
});


const TABLE_STYLES = {
  table: {
    "max-with": "100%"
  },
  selectionCol: {
    "min-width": "3rem",
    "max-with": "3rem",
  },
  subIdCol: {
    "min-width": "20rem",
    "max-with": "20rem",
  },
  planTitleCol: {
    "min-width": "8rem",
    "max-with": "8rem",
    "white-space": "nowrap",
    "overflow": "hidden",
    "text-overflow": "ellipsis",
  },
  billingCycleCol: {
    "min-width": "8rem",
    "max-with": "8rem"
  },
  createdCol: {
    "min-width": "8rem",
    "max-with": "8rem",
  },
  nextBillingCol: {
    "min-width": "8rem",
    "max-with": "8rem",
  },
  statusCol: {
    "min-width": "8rem",
    "max-with": "8rem",
  },
  toolbarCol: {
    "min-width": "7rem",
    "max-with": "7rem",
  },
}
</script>

<template>
  <div class="w-full">
    <div class="card mt-2 table-height table-width">
      <DataTable
          v-model:selection="selected"
          :value="subscriptions"
          dataKey="id"
          scrollable
          scrollHeight="flex"
          size="small"
          :virtualScrollerOptions="{ itemSize: 46 }"
          :style="TABLE_STYLES.table"
      >
        <Column selectionMode="multiple" :style="TABLE_STYLES.selectionCol"></Column>
        <Column field="" header="SubscriberId" :style="TABLE_STYLES.subIdCol">
          <template #body="slotProps">
            <copy-wrapper :text-for-copy="slotProps.data.subscriberId" message-after="SubscriberID copied">
              {{ slotProps.data.subscriberId }}
            </copy-wrapper>
          </template>
        </Column>
        <Column field="planInfo.title" header="Plan" :style="TABLE_STYLES.planTitleCol"></Column>
        <Column field="billingInfo.billingCycle" header="Billing cycle" :style="TABLE_STYLES.billingCycleCol">
          <template #body="slotProps">
            {{ capitalize(slotProps.data.billingInfo.billingCycle) }}
          </template>
        </Column>
        <Column field="" header="Created" :style="TABLE_STYLES.createdCol">
          <template #body="slotProps">
            {{ slotProps.data.createdAt.toLocaleDateString() }}
          </template>
        </Column>
        <Column field="" header="Next billing" :style="TABLE_STYLES.nextBillingCol">
          <template #body="slotProps">
            {{ dateToString(getNextBilling(slotProps.data)) }}
          </template>
        </Column>
        <Column field="status" header="Status" :style="TABLE_STYLES.statusCol">
          <template #body="slotProps">
            <status-tag :status="slotProps.data.status"/>
          </template>
        </Column>
        <Column :style="TABLE_STYLES.toolbarCol">
          <template #header>
            <toolbar-buttons
                @new="createDialog.openDialog()"
                @delete="deleteSelected"
                :disabled-delete="selected.length === 0"
                class="justify-end w-full"
            />
          </template>
          <template #body="slotProps">
            <expanded-menu
                @more="infoDialog.startUpdate(slotProps.data)"
                @edit="updateDialog.startUpdate(slotProps.data)"
                @delete="deleteOne(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Drawer v-model:visible="infoDialog.state.showFlag" position="right" style="width: 60rem;">
      <subscription-info :subscription="infoDialog.state.target" v-if="infoDialog.state.target"/>
    </Drawer>

    <Dialog header="New subscription" v-model:visible="createDialog.state.showFlag" modal>
      <subscription-form
          @submit="saveCreated"
          @cancel="createDialog.closeDialog()"
          mode="create"
      />
    </Dialog>

    <Dialog header="Update subscription" v-model:visible="updateDialog.state.showFlag" modal>
      <subscription-form
          v-if="updateDialog.state.target"
          mode="update"
          :init-data="subMapper.toSubUpdate(updateDialog.state.target)"
          @submit="saveUpdated"
          @cancel="updateDialog.finishUpdate()"
      />
    </Dialog>
  </div>
</template>


<style scoped>
.table-height {
  height: calc(100vh - 14rem)
}

.table-width {
  max-width: 100%;
}
</style>