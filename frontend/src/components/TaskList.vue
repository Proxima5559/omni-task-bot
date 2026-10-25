<script setup lang="ts">
import { useTasksStore } from '@/stores/tasks'
import { timeAgo } from '@/utils/time'
import StatusToggle from './StatusToggle.vue'

const store = useTasksStore()
const SOURCE = { text: '💬 Telegram', voice: '🎙 Voice', web: '🖥 Web' } as const
</script>

<template>
  <div class="table-wrap">
    <table class="table task-table">
      <thead>
        <tr><th>Task</th><th>Source</th><th>Status</th><th>Created</th><th /></tr>
      </thead>
      <tbody>
        <tr v-for="t in store.sorted" :key="t.id" :class="{ 'is-fresh': store.freshIds.includes(t.id) }">
          <td>
            <span v-if="t.transcription_status === 'processing'" class="transcribing"><span class="spinner" /> Transcribing…</span>
            <span v-else-if="t.transcription_status === 'failed'" style="color: var(--danger-text)">
              Transcription failed<span v-if="t.transcription_error"> — {{ t.transcription_error }}</span>
            </span>
            <span v-else :class="{ 'task-title': true, 'is-done': t.status === 'completed' }">{{ t.title }}</span>
          </td>
          <td><span class="source-tag">{{ SOURCE[t.source] }}</span></td>
          <td>
            <StatusToggle
              :model-value="t.status"
              :disabled="t.transcription_status === 'processing' || t.transcription_status === 'failed'"
              @change="store.setStatus(t.id, $event)"
            />
          </td>
          <td class="has-text-grey">{{ timeAgo(t.created_at) }}</td>
          <td><button class="icon-btn" type="button" aria-label="Delete task" @click="store.removeTask(t.id)">✕</button></td>
        </tr>
        <tr v-if="!store.sorted.length"><td colspan="5" class="empty">No tasks yet</td></tr>
      </tbody>
    </table>
  </div>
</template>
