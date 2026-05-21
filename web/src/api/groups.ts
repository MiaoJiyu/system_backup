import request from './request'
import type { Group } from '@/types'

export function getGroups(): Promise<Group[]> {
  return request.get('/groups')
}

export function createGroup(data: Partial<Group>): Promise<Group> {
  return request.post('/groups', data)
}

export function updateGroup(id: number, data: Partial<Group>): Promise<Group> {
  return request.put(`/groups/${id}`, data)
}

export function deleteGroup(id: number): Promise<void> {
  return request.delete(`/groups/${id}`)
}
