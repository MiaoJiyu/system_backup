export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  created_at: string
}

export interface Client {
  id: number
  uuid: string
  ip_address: string | null
  user_id: number | null
  group_id: number | null
  tags: string[]
  status: 'online' | 'offline'
  last_seen: string | null
  os_version: string | null
  client_version: string | null
  config_status: string | null
  created_at: string
  group?: Group | null
  user?: User | null
}

export interface Group {
  id: number
  name: string
  parent_id: number | null
  description: string | null
  created_at: string
  children?: Group[]
  policies?: PolicyTemplate[]
}

export interface Tag {
  id: number
  name: string
}

export interface Storage {
  id: number
  name: string
  type: 'local' | 's3' | 'sftp'
  config: Record<string, any>
  enabled: boolean
  created_at: string
}

export interface PolicyTemplate {
  id: number
  name: string
  description: string | null
  backup_directories: string[]
  backup_usb: boolean
  incremental: boolean
  backup_meta_log: boolean
  schedule_type: 'cron' | 'interval' | 'manual'
  schedule_config: Record<string, any> | null
  upload_storage_id: number | null
  server_address: string | null
  server_port: number | null
  encryption_enabled: boolean
  compression_enabled: boolean
  version_update_policy: 'force' | 'after_task' | 'idle'
  created_at: string
  upload_storage?: Storage | null
}

export interface BackupRecord {
  id: number
  client_id: number
  source_device: string | null
  file_count: number
  total_size: number
  status: 'in_progress' | 'completed' | 'failed'
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  storage_id: number | null
  storage_path: string | null
}

export interface ClientVersion {
  id: number
  version: string
  file_name: string | null
  file_size: number | null
  download_url: string | null
  mirror_url: string | null
  uploaded_by: number | null
  changelog: string | null
  created_at: string
}

export interface ClientLog {
  id: number
  client_id: number
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'
  message: string
  created_at: string
}

export interface SystemStatus {
  online_clients: number
  total_clients: number
  total_backups_today: number
  total_storages: number
  version: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface WSMessage {
  type: string
  request_id?: string
  payload: Record<string, any>
}
