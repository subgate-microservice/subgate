<script setup lang="ts">
import {ref, onMounted, Ref} from 'vue';
import {DataTable, Column} from "primevue";
import {useTopMenu} from "../components/shared/top-menu";
import {ToolbarButtons} from "../components/shared/toolbar-menu";
import {findAndDelete, findAndReplace} from "../../utils/array-utils.ts";
import {ExpandedMenu} from "../components/shared/settings-menu";
import {
  convertFormDataToWebhook, convertWebhookToFormData, createWebhook,
  deleteSelectedWebhooks,
  deleteWebhookById, getSelectedWebhooks,
  updateWebhook,
  Webhook,
  WebhookFormData
} from "../../webhook";
import {WebhookForm} from "../components/webhook/webhook-form";
import {CopyWrapper} from "../components/shared/copy-button";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Webhooks"

const items: Ref<Webhook[]> = ref([])


// Create subscription
const showCreateDialog = ref(false)
const startCreating = () => {
  showCreateDialog.value = true
}
const cancelCreating = () => {
  showCreateDialog.value = false
}
const saveCreated = async (item: WebhookFormData) => {
  const created = await createWebhook(item)
  items.value = [...items.value, created]
  showCreateDialog.value = false
}


// Update
const showUpdateDialog = ref(false)
const itemForUpdate: Ref<Webhook | null> = ref(null)
const startUpdating = (item: Webhook) => {
  itemForUpdate.value = item
  showUpdateDialog.value = true
}
const cancelUpdating = () => {
  showUpdateDialog.value = false
}
const saveUpdated = async (item: WebhookFormData) => {
  const updatedItem = convertFormDataToWebhook(
      item, itemForUpdate.value!.id, itemForUpdate.value!.createdAt,)
  await updateWebhook(updatedItem)
  findAndReplace(updatedItem, items.value, x => x.id)
  itemForUpdate.value = null
  showUpdateDialog.value = false
}


// Delete
const selected: Ref<Webhook[]> = ref([]);
const deleteOne = async (item: Webhook) => {
  await deleteWebhookById(item.id)
  findAndDelete(item, items.value, x => x.id)
}
const deleteSelected = async () => {
  const sby = {ids: selected.value.map(x => x.id)}
  await deleteSelectedWebhooks(sby)

  const hashes = new Set(sby.ids)
  items.value = items.value.filter(x => !hashes.has(x.id))
  selected.value = []
}


onMounted(async () => {
  items.value = await getSelectedWebhooks({})
});

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
              {{slotProps.data.targetUrl}}
            </copy-wrapper>
          </template>
        </Column>
        <Column field="eventCode" header="Event code" :style="TABLE_STYLES.eventCodeCol">
          <template #body="slotProps">
            <copy-wrapper :text-for-copy="slotProps.data.eventCode" message-after="Event code was copied">
              {{slotProps.data.eventCode}}
            </copy-wrapper>
          </template>
        </Column>

        <Column :style="TABLE_STYLES.toolbarCol">
          <template #header>
            <toolbar-buttons
                @new="startCreating"
                @delete="deleteSelected"
                :disabled-delete="selected.length === 0"
                class="justify-end w-full"
            />
          </template>
          <template #body="slotProps">
            <expanded-menu
                :show-view="false"
                @edit="startUpdating(slotProps.data)"
                @delete="deleteOne(slotProps.data)"
                class="justify-end"
            />
          </template>
        </Column>
      </DataTable>

    </div>
    <Dialog header="New webhook" v-model:visible="showCreateDialog" modal>
      <webhook-form
          @submit="saveCreated"
          @cancel="cancelCreating"
      />
    </Dialog>
    <Dialog header="Update webhook" v-model:visible="showUpdateDialog" modal>
      <webhook-form
          v-if="itemForUpdate"
          :init-data="convertWebhookToFormData(itemForUpdate)"
          @submit="saveUpdated"
          @cancel="cancelUpdating"
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