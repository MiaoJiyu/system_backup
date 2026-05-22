import request from './request'
import type { Group, Client } from '@/types'

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

export function getGroupClients(id: number, params?: Record<string, any>): Promise<Client[]> {
  return request.get(`/groups/${id}/clients`, { params })
}

export function addClientsToGroup(id: number, clientIds: number[]): Promise<any> {
  return request.post(`/groups/${id}/clients`, { client_ids: clientIds })
}

export function removeClientFromGroup(groupId: number, clientId: number): Promise<any> {
  return request.delete(`/groups/${groupId}/clients/${clientId}`)
}
