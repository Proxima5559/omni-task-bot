<script setup lang="ts">
import { STATUSES, type TaskStatus } from '@/types'

defineProps<{ modelValue: TaskStatus; disabled?: boolean }>()
defineEmits<{ change: [status: TaskStatus] }>()
</script>

<template>
  <div class="status-toggle" role="group" aria-label="Task status">
    <button
      v-for="s in STATUSES"
      :key="s.value"
      type="button"
      :class="{ 'is-active': s.value === modelValue }"
      :disabled="disabled"
      :aria-pressed="s.value === modelValue"
      @click="$emit('change', s.value)"
    >
      {{ s.label }}
    </button>
  </div>
</template>
