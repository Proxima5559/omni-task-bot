import { ref } from 'vue'

const now = ref(Date.now())
setInterval(() => (now.value = Date.now()), 30_000)

export function timeAgo(iso: string): string {
  const sec = Math.max(0, Math.round((now.value - Date.parse(iso)) / 1000))
  if (sec < 45) return 'just now'
  if (sec < 3600) return `${Math.round(sec / 60)}m ago`
  if (sec < 86400) return `${Math.round(sec / 3600)}h ago`
  return new Date(iso).toLocaleDateString()
}
