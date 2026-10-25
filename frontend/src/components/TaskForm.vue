<script setup lang="ts">
import { ref } from 'vue'
import { useTasksStore } from '@/stores/tasks'

const store = useTasksStore()
const title = ref('')
const description = ref('') 
const busy = ref(false)

async function submit() {
  const titleValue = title.value.trim()
  const descValue = description.value.trim()
  
  if (!titleValue || busy.value) return
  
  busy.value = true
  await store.createTask(titleValue, descValue || undefined) 
  
  title.value = ''
  description.value = '' 
  busy.value = false
}
</script>

<template>
  <form class="field" @submit.prevent="submit">
    <div class="control">
      <input 
        v-model="title" 
        class="input" 
        type="text" 
        maxlength="500" 
        placeholder="Add a task… (or send it to the Telegram bot)" 
      />
    </div>
    
    <div class="control mt-2">
      <textarea 
        v-model="description" 
        class="textarea" 
        placeholder="Add a description… (optional)"
        rows="2"
      ></textarea>
    </div>

    <div class="control mt-2 is-clearfix">
      <button 
        class="button btn-accent is-pulled-right" 
        :class="{ 'is-loading': busy }" 
        :disabled="!title.trim()"
      >
        Add Task
      </button>
    </div>
  </form>
</template>
