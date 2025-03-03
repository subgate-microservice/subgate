<template>
 <pre class="my-pre">{{ p.data}}</pre>
</template>

<script lang="ts" setup>
type DataObject = Record<string, any>;

const p = defineProps<{
  data: DataObject,
}>()


</script>

<style scoped>
.my-pre {
  background-color: #3b4252 ;
  color: white;
  font-family: "Roboto Mono", Courier, monospace;
  font-size: 16px;
  line-height: 1.6;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  border: 1px solid #4c566a;
}

.key {
  color: #88c0d0;
  font-weight: bold;
}

.value {
  color: #a3be8c;
}

.symbol {
  color: #ebcb8b;
}
</style>
