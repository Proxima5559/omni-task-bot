export type TaskStatus = 'pending' | 'in_progress' | 'completed'
export type TaskSource = 'text' | 'voice' | 'web'
export type TranscriptionStatus = 'not_required' | 'processing' | 'done' | 'failed'

export interface Task {
  id: number
  user_id: number | null
  title: string
  description: string | null
  status: TaskStatus
  source: TaskSource
  transcription_status: TranscriptionStatus
  transcription_error: string | null
  created_at: string
  updated_at: string
}

export interface TaskEvent {
  type: 'task.created' | 'task.updated' | 'task.deleted'
  task: Task
}

export const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
]
