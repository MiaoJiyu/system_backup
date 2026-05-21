import request from './request'
import type { Tag } from '@/types'

export function getTags(): Promise<Tag[]> {
  return request.get('/tags')
}

export function createTag(data: { name: string }): Promise<Tag> {
  return request.post('/tags', data)
}

export function deleteTag(id: number): Promise<void> {
  return request.delete(`/tags/${id}`)
}
