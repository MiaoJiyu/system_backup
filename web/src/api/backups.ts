import request from './request'
import type { BackupRecord, PaginatedResponse } from '@/types'

export function getBackups(params?: Record<string, any>): Promise<PaginatedResponse<BackupRecord>> {
  return request.get('/backups', { params })
}

export function getBackup(id: number): Promise<BackupRecord> {
  return request.get(`/backups/${id}`)
}
