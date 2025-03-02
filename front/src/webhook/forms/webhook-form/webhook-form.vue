<script setup lang="ts">

import EventSelector from "./event-selector.vue";

const e = defineEmits(["submit", "cancel"])

const onSubmit = async () => {

}

const onCancel = async () => {

}
</script>

<template>
  <div class="w-[30rem] h-full">
    <div class="flex flex-wrap gap-4 h-full">
      <div class="flex flex-col gap-3 flex-1">
        <div>
          <IftaLabel class="w-full">
            <InputText
                class="w-full"
                id="urlInput"
            />
            <label for="urlInput">Url</label>
          </IftaLabel>
        </div>

        <event-selector/>

        <div class="flex flex-wrap gap-2 mt-2">
          <Button label="Submit" @click="onSubmit"/>
          <Button label="Cancel" outlined @click="onCancel"/>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>

</style>