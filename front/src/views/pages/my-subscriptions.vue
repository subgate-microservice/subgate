<script setup lang="ts">
import {ref, onMounted, Ref} from 'vue';
import {DataTable, Column, Drawer} from "primevue";

import {
  deleteSelectedSubscriptions,
  deleteSubscriptionById,
} from "../../subscription/usecases.ts";
import {SubscriptionInfo} from "../components/subscription/subscription-info";
import {useTopMenu} from "../components/shared/top-menu";
import {ToolbarButtons} from "../components/shared/toolbar-menu";
import {findAndDelete, findAndReplace} from "../../utils/array-utils.ts";
import {ExpandedMenu} from "../components/shared/settings-menu";
import {CopyWrapper} from "../components/shared/copy-button";
import {StatusTag} from "../components/subscription/status-tag";
import {useCreateDialogManager, useUpdateDialogManager} from "../../core/services.ts";
import {SubscriptionRepo} from "../../core/repositories.ts";
import {Subscription, SubscriptionUpdate} from "../../core/domain.ts";
import {SubscriptionMapper} from "../../core/mappers.ts";
import {SubscriptionForm} from "../components/subscription/subcription-form";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Subscriptions"

const subRepo = new SubscriptionRepo()
const subMapper = new SubscriptionMapper()

const subscriptions: Ref<Subscription[]> = ref([])

const createDialog = useCreateDialogManager()
const updateDialog = useUpdateDialogManager<Subscription>()


const saveCreated = async (item: SubscriptionUpdate) => {
  const created = await subRepo.create(item)
  subscriptions.value = [...subscriptions.value, created]
  createDialog.closeDialog()
}

// View subscription
const showInfoWindow = ref(false)
const itemFowFullInfo: Ref<Subscription | null> = ref(null)
const openFullInfo = (item: Subscription) => {
  itemFowFullInfo.value = item
  showInfoWindow.value = true
}


const saveUpdated = async (item: SubscriptionUpdate) => {
  const updated = await subRepo.update(item)
  findAndReplace(updated, subscriptions.value, x => x.id)
  updateDialog.finishUpdate()
}


// Delete subscription
const selected: Ref<Subscription[]> = ref([]);
const deleteOne = async (item: Subscription) => {
  await deleteSubscriptionById(item.id)
  findAndDelete(item, subscriptions.value, x => x.id)
}
const deleteSelected = async () => {
  const sby = {ids: selected.value.map(x => x.id)}
  await deleteSelectedSubscriptions(sby)

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
        <Column field="plan.title" header="Plan" :style="TABLE_STYLES.planTitleCol"></Column>
        <Column field="plan.billingCycle.title" header="Billing cycle" :style="TABLE_STYLES.billingCycleCol"></Column>
        <Column field="" header="Created" :style="TABLE_STYLES.createdCol">
          <template #body="slotProps">
            {{ slotProps.data.createdAt.toLocaleDateString() }}
          </template>
        </Column>
        <Column field="" header="Next billing" :style="TABLE_STYLES.nextBillingCol">
          <template #body="slotProps">
            Next Billing Date
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
                @more="openFullInfo(slotProps.data)"
                @edit="updateDialog.startUpdate(slotProps.data)"
                @delete="deleteOne(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Drawer v-model:visible="showInfoWindow" position="right" style="width: 60rem;">
      <subscription-info :subscription="itemFowFullInfo" v-if="itemFowFullInfo"/>
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