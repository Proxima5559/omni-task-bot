<script setup lang="ts">
import type { Task } from '@/types'
import TaskCard from './TaskCard.vue'

defineProps<{ label: string; tasks: Task[] }>()
</script>

<template>
  <section class="column">
    <header class="column-head">
      <h2>{{ label }}</h2>
      <span class="count">{{ tasks.length }}</span>
    </header>
    <TaskCard v-for="t in tasks" :key="t.id" :task="t" />
    <p v-if="!tasks.length" class="empty">Nothing here</p>
  </section>
</template>
