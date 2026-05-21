import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSystemStatus } from '@/api/system'
import type { SystemStatus } from '@/types'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const systemStatus = ref<SystemStatus | null>(null)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  async function fetchSystemStatus() {
    try {
      systemStatus.value = await getSystemStatus()
    } catch {
      console.error('Failed to fetch system status')
    }
  }

  return { sidebarCollapsed, systemStatus, toggleSidebar, fetchSystemStatus }
})
