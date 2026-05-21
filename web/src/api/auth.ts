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
