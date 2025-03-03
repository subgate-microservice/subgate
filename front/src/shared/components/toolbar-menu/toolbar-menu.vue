<script setup lang="ts">

const searchValue = defineModel("search", {default: "",})

const e = defineEmits<{
  (e: "new"): void,
  (e: "delete"): void,
}>()

interface P {
  disabledDelete?: boolean,
}

const p = withDefaults(defineProps<P>(), {
  disabledDelete: false,
})

const clickOnNewBtn = () => e("new")
const clickOnDeleteBtn = () => e("delete")
</script>

<template>
  <Toolbar>
    <template #start>
      <IconField>
        <InputIcon class="pi pi-search"/>
        <InputText v-model="searchValue" placeholder="Search" type="search"/>
      </IconField>

    </template>

    <template #center>
    </template>

    <template #end>
      <div class="flex flex-wrap gap-2">
        <Button
            label="New"
            icon="pi pi-plus"
            @click="clickOnNewBtn"
        />
        <Button
            label="Delete"
            icon="pi pi-trash"
            @click="clickOnDeleteBtn"
            severity="danger"
            :disabled="p.disabledDelete"
            outlined
        />
      </div>
    </template>
  </Toolbar>
</template>

<style scoped>

</style>