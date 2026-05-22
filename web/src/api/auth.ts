import request from './request'
import type { LoginRequest, LoginResponse, User } from '@/types'

export function login(data: LoginRequest): Promise<LoginResponse> {
  return request.post('/auth/login', data)
}

export function register(data: { username: string; password: string; role?: string }): Promise<User> {
  return request.post('/auth/register', data)
}

export function getMe(): Promise<User> {
  return request.get('/auth/me')
}

export function changePassword(data: { old_password: string; new_password: string }): Promise<any> {
  return request.post('/auth/change-password', data)
}

export function getUsers(): Promise<User[]> {
  return request.get('/users')
}

export function updateUser(id: number, data: Partial<User & { password: string }>): Promise<User> {
  return request.put(`/users/${id}`, data)
}

export function deleteUser(id: number): Promise<void> {
  return request.delete(`/users/${id}`)
}
