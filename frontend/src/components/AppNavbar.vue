<script setup lang="ts">
import { computed } from 'vue'
import { useTasksStore } from '@/stores/tasks'

const store = useTasksStore()
const label = computed(() => ({ live: 'Live', connecting: 'Connecting…', offline: 'Offline — retrying' })[store.connection])
</script>

<template>
  <nav class="navbar app-navbar" aria-label="main navigation">
    <div class="container-wide" style="display: flex; align-items: center; justify-content: space-between; padding-top: .75rem; padding-bottom: .75rem">
      <span class="brand is-size-5">Omni<span>Tasks</span></span>
      <span class="live-pill" :class="`is-${store.connection}`" role="status">
        <span class="dot" /> {{ label }}
      </span>
    </div>
  </nav>
</template>
