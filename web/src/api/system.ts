import request from './request'
import type { SystemStatus } from '@/types'

export function getSystemStatus(): Promise<SystemStatus> {
  return request.get('/system/status')
}

export function initDatabase(data: { database_url: string }): Promise<void> {
  return request.post('/system/init-db', data)
}
