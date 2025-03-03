<script setup lang="ts">
interface P {
  validationErrors?: string[]
}

const p = withDefaults(defineProps<P>(), {
  validationErrors: () => [],
})

const modelValue = defineModel({default: ""})
</script>

<template>
  <div class="w-full h-[10rem]">
    <IftaLabel class="h-full">
          <Textarea
              id="json_input"
              v-model="modelValue"
              style="resize: none;"
              class="w-full h-full"
              placeholder="Enter json data"
          />
      <label for="json_input">Fields</label>
    </IftaLabel>
    <Message severity="error" size="small" variant="simple" v-for="err in p.validationErrors" class="mt-1">
      {{ err }}
    </Message>
  </div>
</template>

<style scoped>

</style>