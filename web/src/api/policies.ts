import request from './request'
import type { PolicyTemplate, PaginatedResponse } from '@/types'

export function getPolicies(params?: Record<string, any>): Promise<PaginatedResponse<PolicyTemplate>> {
  return request.get('/policies', { params })
}

export function createPolicy(data: Partial<PolicyTemplate>): Promise<PolicyTemplate> {
  return request.post('/policies', data)
}

export function updatePolicy(id: number, data: Partial<PolicyTemplate>): Promise<PolicyTemplate> {
  return request.put(`/policies/${id}`, data)
}

export function deletePolicy(id: number): Promise<void> {
  return request.delete(`/policies/${id}`)
}

export function assignPolicy(data: {
  group_id?: number
  tag_id?: number
  client_id?: number
  policy_template_id: number
  priority?: number
  override_config?: Record<string, any>
}): Promise<void> {
  return request.post('/policies/assign', data)
}

export function getAssignments(params?: Record<string, any>): Promise<any> {
  return request.get('/policies/assignments', { params })
}

export function removeAssignment(type: string, id: number): Promise<void> {
  return request.delete(`/policies/assignments/${type}/${id}`)
}
