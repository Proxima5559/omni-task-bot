<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { STATUSES } from '@/types'
import { useTasksStore } from '@/stores/tasks'
import TaskForm from '@/components/TaskForm.vue'
import TaskBoard from '@/components/TaskBoard.vue'
import TaskList from '@/components/TaskList.vue'

type Layout = 'board' | 'list'
const store = useTasksStore()

const stored = localStorage.getItem('layout')
const layout = ref<Layout>(stored === 'list' ? 'list' : 'board')
watch(layout, (v) => localStorage.setItem('layout', v))

onMounted(() => {
  void store.fetchTasks()
  store.connect()
})
onUnmounted(() => store.disconnect())
</script>

<template>
  <main class="container-wide">
    <div class="mb-4"><TaskForm /></div>

    <div v-if="store.error" class="notification error-banner">
      <button class="delete" aria-label="Dismiss" @click="store.error = null" />
      {{ store.error }}
    </div>

    <div class="is-flex is-align-items-center is-justify-content-space-between is-flex-wrap-wrap mb-4" style="gap: .75rem">
      <div class="is-flex is-flex-wrap-wrap" style="gap: .5rem">
        <span v-for="s in STATUSES" :key="s.value" class="stat">{{ s.label }}<b>{{ store.byStatus[s.value].length }}</b></span>
      </div>
      <div class="buttons has-addons mb-0">
        <button class="button is-small btn-ghost" :class="{ 'is-active': layout === 'board' }" @click="layout = 'board'">Board</button>
        <button class="button is-small btn-ghost" :class="{ 'is-active': layout === 'list' }" @click="layout = 'list'">List</button>
      </div>
    </div>

    <p v-if="store.loading && !store.tasks.length" class="empty">Loading tasks…</p>
    <TaskBoard v-else-if="layout === 'board'" />
    <TaskList v-else />
  </main>
</template>
