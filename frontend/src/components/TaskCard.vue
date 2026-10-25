<script setup lang="ts">
import { computed } from 'vue'
import type { Task } from '@/types'
import { useTasksStore } from '@/stores/tasks'
import { timeAgo } from '@/utils/time'
import StatusToggle from './StatusToggle.vue'

const props = defineProps<{ task: Task }>()
const store = useTasksStore()

const processing = computed(() => props.task.transcription_status === 'processing')
const failed = computed(() => props.task.transcription_status === 'failed')
const fresh = computed(() => store.freshIds.includes(props.task.id))
const source = computed(() => ({ text: '💬 Telegram', voice: '🎙 Voice', web: '🖥 Web' })[props.task.source])
</script>

<template>
  <article class="task-card" :class="{ 'is-fresh': fresh }">
    <div class="task-meta">
      <span class="source-tag">{{ source }}</span>
      <span>{{ timeAgo(task.created_at) }}</span>
    </div>

    <div v-if="processing" class="transcribing">
      <span class="spinner" aria-hidden="true" /> Transcribing voice message…
    </div>
    <div v-else-if="failed" class="failed-box">
      <strong>Couldn't transcribe this voice message.</strong>
      <div v-if="task.transcription_error">{{ task.transcription_error }}</div>
    </div>
    <template v-else>
      <div class="task-title" :class="{ 'is-done': task.status === 'completed' }">{{ task.title }}</div>
      <p v-if="task.description" class="task-desc">{{ task.description }}</p>
    </template>

    <div class="task-actions">
      <StatusToggle
        :model-value="task.status"
        :disabled="processing || failed"
        @change="store.setStatus(task.id, $event)"
      />
      <button class="icon-btn" type="button" title="Delete task" aria-label="Delete task" @click="store.removeTask(task.id)">✕</button>
    </div>
  </article>
</template>
