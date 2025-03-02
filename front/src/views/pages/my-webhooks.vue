<script setup lang="ts">
import {ref, onMounted, Ref} from 'vue';
import {DataTable, Column} from "primevue";
import {useTopMenu} from "../components/shared/top-menu";
import {ToolbarButtons} from "../components/shared/toolbar-menu";
import {findAndDelete, findAndReplace} from "../../utils/array-utils.ts";
import {ExpandedMenu} from "../components/shared/settings-menu";
import {CopyWrapper} from "../components/shared/copy-button";
import {Webhook, WebhookCU} from "../../webhook/domain.ts";
import {useCreateDialogManager, useUpdateDialogManager} from "../../utils/dialog-manager.ts";
import {WebhookRepo} from "../../webhook/repositories.ts";
import WebhookForm from "../../webhook/forms/webhook-form/webhook-form.vue";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Webhooks"

const items: Ref<Webhook[]> = ref([])
const webhookRepo = new WebhookRepo()

const createDialog = useCreateDialogManager()
const updateDialog = useUpdateDialogManager<Webhook>()


const saveCreated = async (item: WebhookCU) => {
  const created = await webhookRepo.createOne(item)
  items.value = [...items.value, created]
  createDialog.closeDialog()
}


// Update
const saveUpdated = async (item: WebhookCU) => {
  const updated = await webhookRepo.updateOne(item)
  findAndReplace(updated, items.value, x => x.id)
  updateDialog.finishUpdate()
}


// Delete
const selected: Ref<Webhook[]> = ref([]);
const deleteOne = async (item: Webhook) => {
  await webhookRepo.deleteById(item.id)
  findAndDelete(item, items.value, x => x.id)
}
const deleteSelected = async () => {
  const sby = {ids: selected.value.map(x => x.id)}
  console.warn("NOT_IMPLEMENTED!")
  const hashes = new Set(sby.ids)
  items.value = items.value.filter(x => !hashes.has(x.id))
  selected.value = []
}


onMounted(async () => {
  items.value = await webhookRepo.getAll()
})

const TABLE_STYLES = {
  table: {
    "max-with": "100%"
  },
  selectionCol: {
    "min-width": "3rem",
    "max-with": "3rem"
  },
  urlCol: {
    "min-width": "24rem",
    "max-with": "24rem",
    "white-space": "nowrap",
    "overflow": "hidden",
    "text-overflow": "ellipsis",
  },
  eventCodeCol: {
    "min-width": "18rem",
    "max-with": "18rem"
  },
  // rollbackModeCol: {
  //   "min-width": "18rem",
  //   "max-with": "18rem"
  // },
  toolbarCol: {
    "min-width": "7rem",
    "max-with": "7rem"
  },
}
</script>

<template>
  <div class="w-full">
    <div class="card mt-2 table-height table-width">
      <DataTable
          v-model:selection="selected"
          :value="items"
          dataKey="id"
          scrollable
          scrollHeight="flex"
          size="small"
          :style="TABLE_STYLES.table"
      >
        <Column selectionMode="multiple" :style="TABLE_STYLES.selectionCol"></Column>
        <Column field="targetUrl" header="Url" :style="TABLE_STYLES.urlCol">
          <template #body="slotProps">
            <copy-wrapper :text-for-copy="slotProps.data.targetUrl" message-after="Url was copied">
              {{ slotProps.data.targetUrl }}
            </copy-wrapper>
          </template>
        </Column>
        <Column field="eventCode" header="Event code" :style="TABLE_STYLES.eventCodeCol">
          <template #body="slotProps">
            <copy-wrapper :text-for-copy="slotProps.data.eventCode" message-after="Event code was copied">
              {{ slotProps.data.eventCode }}
            </copy-wrapper>
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
                :show-view="false"
                @edit="updateDialog.startUpdate(slotProps.data)"
                @delete="deleteOne(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Dialog header="New webhook" modal v-model:visible="createDialog.state.showFlag">
      <webhook-form
          @submit="saveCreated"
          @cancel="createDialog.closeDialog()"
      />
    </Dialog>
    <Dialog header="Update webhook" modal v-model:visible="updateDialog.state.showFlag">
      <webhook-form
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