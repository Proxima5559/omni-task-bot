import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { tasksApi } from '@/api/tasks'
import { errorMessage } from '@/api/client'
import type { Task, TaskEvent, TaskStatus } from '@/types'

export type Connection = 'connecting' | 'live' | 'offline'

const FRESH_MS = 3000
const MAX_BACKOFF_MS = 15_000

function wsUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/tasks`
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const connection = ref<Connection>('offline')
  const freshIds = ref<number[]>([]) 

  const sorted = computed(() => [...tasks.value].sort((a, b) => b.id - a.id))
  const byStatus = computed(() => {
    const groups: Record<TaskStatus, Task[]> = { pending: [], in_progress: [], completed: [] }
    for (const t of sorted.value) groups[t.status].push(t)
    return groups
  })

  function markFresh(id: number) {
    if (!freshIds.value.includes(id)) freshIds.value = [...freshIds.value, id]
    setTimeout(() => (freshIds.value = freshIds.value.filter((x) => x !== id)), FRESH_MS)
  }

  function upsert(task: Task) {
    const i = tasks.value.findIndex((t) => t.id === task.id)
    if (i === -1) {
      tasks.value.push(task)
      markFresh(task.id)
    } else {
      tasks.value[i] = task
    }
  }

  function remove(id: number) {
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  async function fetchTasks() {
    loading.value = true
    try {
      tasks.value = await tasksApi.list()
      error.value = null
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function createTask(title: string, description?: string) {
    try {
      upsert(await tasksApi.create(title, description || undefined))
      error.value = null
    } catch (e) {
      error.value = errorMessage(e)
    }
  }

  async function setStatus(id: number, status: TaskStatus) {
    const task = tasks.value.find((t) => t.id === id)
    if (!task || task.status === status) return
    const previous = task.status
    task.status = status
    try {
      upsert(await tasksApi.setStatus(id, status))
    } catch (e) {
      const t = tasks.value.find((x) => x.id === id)
      if (t) t.status = previous
      error.value = errorMessage(e)
    }
  }

  async function removeTask(id: number) {
    const snapshot = tasks.value
    remove(id)
    try {
      await tasksApi.remove(id)
    } catch (e) {
      tasks.value = snapshot
      error.value = errorMessage(e)
    }
  }

  let socket: WebSocket | null = null
  let retries = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let wantOpen = false

  function handleEvent(event: TaskEvent) {
    if (event.type === 'task.deleted') remove(event.task.id)
    else upsert(event.task)
  }

  function connect() {
    wantOpen = true
    if (socket && socket.readyState <= WebSocket.OPEN) return 
    connection.value = 'connecting'
    socket = new WebSocket(wsUrl())

    socket.onopen = () => {
      retries = 0
      connection.value = 'live'
      void fetchTasks() 
    }
    socket.onmessage = (msg) => {
      try {
        handleEvent(JSON.parse(msg.data) as TaskEvent)
      } catch {
        console.warn('Ignoring malformed WebSocket message', msg.data)
      }
    }
    socket.onerror = () => socket?.close()
    socket.onclose = () => {
      connection.value = 'offline'
      socket = null
      if (!wantOpen) return
      const delay = Math.min(1000 * 2 ** retries++, MAX_BACKOFF_MS)
      timer = setTimeout(connect, delay)
    }
  }

  function disconnect() {
    wantOpen = false
    clearTimeout(timer)
    socket?.close()
    socket = null
    connection.value = 'offline'
  }

  return {
    tasks, loading, error, connection, freshIds, sorted, byStatus,
    fetchTasks, createTask, setStatus, removeTask, connect, disconnect,
  }
})
