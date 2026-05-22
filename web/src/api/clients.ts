import request from './request'
import type { Client, ClientLog, PaginatedResponse, BackupRecord } from '@/types'

export function getClients(params?: Record<string, any>): Promise<PaginatedResponse<Client>> {
  return request.get('/clients', { params })
}

export function getClient(id: number): Promise<Client> {
  return request.get(`/clients/${id}`)
}

export function updateClient(id: number, data: Partial<Client>): Promise<Client> {
  return request.patch(`/clients/${id}`, data)
}

export function deleteClient(id: number): Promise<void> {
  return request.delete(`/clients/${id}`)
}

export function sendCommand(id: number, command: string, payload?: Record<string, any>): Promise<void> {
  return request.post(`/clients/${id}/command`, { command, payload })
}

export function getClientLogs(id: number, params?: Record<string, any>): Promise<PaginatedResponse<ClientLog>> {
  return request.get(`/clients/${id}/logs`, { params })
}

export function getClientBackups(id: number, params?: Record<string, any>): Promise<PaginatedResponse<BackupRecord>> {
  return request.get(`/clients/${id}/backups`, { params })
}

export function getEffectivePolicy(id: number): Promise<Record<string, any>> {
  return request.get(`/clients/${id}/effective-policy`)
}

export function pushClientConfig(id: number, data: { config?: Record<string, any>; policy_template_id?: number }): Promise<any> {
  return request.patch(`/clients/${id}/config`, data)
}
