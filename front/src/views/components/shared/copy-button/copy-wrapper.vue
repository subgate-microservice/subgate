<script setup lang="ts">
import {useToast} from "primevue";

interface P {
  textForCopy: string,
  messageAfter?: string,
}

const toast = useToast()

const p = withDefaults(defineProps<P>(), {
  messageAfter: "Was copied",
})


const onClick = async () => {
  await navigator.clipboard.writeText(p.textForCopy);
  toast.add({severity: "info", summary: p.messageAfter, life: 3000})
}
</script>

<template>
  <div
      @click="onClick"
      class="cursor-pointer hover:underline w-max"
  >
    <slot>

    </slot>
  </div>
</template>

<style scoped>

</style>