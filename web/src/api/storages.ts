import request from './request'
import type { Storage } from '@/types'

export function getStorages(): Promise<Storage[]> {
  return request.get('/storages')
}

export function createStorage(data: Partial<Storage>): Promise<Storage> {
  return request.post('/storages', data)
}

export function updateStorage(id: number, data: Partial<Storage>): Promise<Storage> {
  return request.put(`/storages/${id}`, data)
}

export function deleteStorage(id: number): Promise<void> {
  return request.delete(`/storages/${id}`)
}

export function testStorage(id: number): Promise<{ success: boolean; message: string }> {
  return request.post(`/storages/${id}/test`)
}
