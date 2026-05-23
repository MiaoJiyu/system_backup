import request from './request'
import type { ClientVersion, PaginatedResponse } from '@/types'

export function getVersions(params?: Record<string, any>): Promise<PaginatedResponse<ClientVersion>> {
  return request.get('/versions', { params })
}

export function uploadVersion(formData: FormData): Promise<ClientVersion> {
  return request.post('/versions', formData)
}

export function updateVersion(id: number, data: Partial<ClientVersion>): Promise<ClientVersion> {
  return request.put(`/versions/${id}`, data)
}

export function deleteVersion(id: number): Promise<void> {
  return request.delete(`/versions/${id}`)
}

export function pushVersion(id: number, clientIds: number[]): Promise<void> {
  return request.post(`/versions/${id}/push`, { client_ids: clientIds })
}
