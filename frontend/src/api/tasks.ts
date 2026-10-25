import { http } from './client'
import type { Task, TaskStatus } from '@/types'

export const tasksApi = {
  list: async (): Promise<Task[]> => (await http.get<Task[]>('/tasks', { params: { limit: 200 } })).data,
  
  create: async (title: string, description?: string): Promise<Task> => 
    (await http.post<Task>('/tasks', { 
      title, 
      description: description || null 
    })).data,
    
  setStatus: async (id: number, status: TaskStatus): Promise<Task> =>
    (await http.patch<Task>(`/tasks/${id}/status`, { status })).data,
    
  remove: async (id: number): Promise<void> => {
    await http.delete(`/tasks/${id}`)
  },
}