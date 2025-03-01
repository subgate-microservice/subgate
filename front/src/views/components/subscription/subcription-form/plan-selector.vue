<script setup lang="ts">
import {onMounted, ref, Ref} from "vue";
import {
  Plan,
} from "../../../../core/domain.ts";
import {PlanRepo} from "../../../../core/repositories.ts";


const allPlans: Ref<Plan[]> = ref([])


onMounted(async () => {
  allPlans.value = await new PlanRepo().getAll()
})

const selectedPlan = defineModel({default: null})

</script>

<template>
  <div>
    <IftaLabel>
      <Select
          id="PlanSelector"
          option-label="title"
          v-model="selectedPlan"
          :options="allPlans"
          class="w-full"
      />
      <label for="PlanSelector">Plan</label>
    </IftaLabel>
  </div>
</template>

<style scoped>

</style>