<script setup lang="ts">
import { STATUSES } from '@/types'
import { useTasksStore } from '@/stores/tasks'
import TaskColumn from './TaskColumn.vue'

const store = useTasksStore()
</script>

<template>
  <div class="board">
    <TaskColumn v-for="s in STATUSES" :key="s.value" :label="s.label" :tasks="store.byStatus[s.value]" />
  </div>
</template>
