<script setup lang="ts">
import {onMounted, ref, Ref} from "vue";
import {useTopMenu} from "../../shared/components/top-menu";
import ApikeyCard from "../components/apikey-card.vue";
import GenerateApikey from "../forms/generate-apikey.vue";
import {Apikey} from "../domain.ts";
import {ApikeyRepo} from "../repositories.ts";


const topMenuStore = useTopMenu()
topMenuStore.headerTitle = "Apikeys"
const apikeyRepo = new ApikeyRepo()

const items: Ref<Apikey[]> = ref([])

const onApikeyCreated = (item: Apikey) => {
  items.value.push(item)
}

const onApikeyDeleted = (item: Apikey) => {
  items.value = items.value.filter(x => x.id !== item.id)
}

onMounted(async () => {
  items.value = await apikeyRepo.getAll()
})
</script>

<template>
  <div class="flex justify-center">
    <div class="flex flex-col gap-2 w-[40rem]">
      <div v-if="items.length === 0">
        There are no apikeys but you can create one right now
      </div>
      <apikey-card
          @apikey-deleted="onApikeyDeleted"
          class="w-full h-max "
          :apikey="item"
          v-for="item in items"
      />
      <generate-apikey @apikey-created="onApikeyCreated" class=""/>
    </div>
  </div>
</template>

<style scoped>

</style>