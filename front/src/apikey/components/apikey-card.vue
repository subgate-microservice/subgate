<script setup lang="ts">
import {dateToString} from "../../shared/services/other.ts";
import {useConfirm} from "primevue/useconfirm";
import {ApikeyRepo} from "../repositories.ts";
import {Apikey} from "../domain.ts";

interface P {
  apikey: Apikey,
}

const p = defineProps<P>()

const e = defineEmits<{
  (e: "apikeyDeleted", item: Apikey): void,
}>()

const confirm = useConfirm()


const onDelete = async () => {
  confirm.require({
    message: 'Do you want to delete this API Key?',
    header: 'Danger Zone',
    icon: 'pi pi-info-circle',
    rejectLabel: 'Cancel',
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true
    },
    acceptProps: {
      label: 'Delete',
      severity: 'contrast'
    },
    accept: async () => {
      await new ApikeyRepo().deleteOneById(p.apikey.publicId)
      e("apikeyDeleted", p.apikey)
    },
    reject: () => {
    }
  });
}


</script>

<template>
  <div class="card flex flex-wrap justify-between apikey-card items-center">
    <div>
      <div class="flex flex-wrap gap-12">
        <div>
          <div class="text-gray-400">
            Title
          </div>
          <div class="font-bold">
            {{ p.apikey.title }}
          </div>
        </div>
        <div>
          <div class="text-gray-400">
            Created
          </div>
          <div>
            {{ dateToString(p.apikey.createdAt) }}
          </div>
        </div>
      </div>

    </div>
    <Button
        size="small"
        severity="contrast"
        label="Delete"
        outlined
        icon="pi pi-trash"
        @click="onDelete"
    />
  </div>
</template>

<style scoped>
.apikey-card {
  padding: 1rem;
}
</style>