import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Client, Tag, Group, PaginatedResponse } from '@/types'
import * as clientsApi from '@/api/clients'
import { getTags } from '@/api/tags'
import { getGroups } from '@/api/groups'

export const useClientsStore = defineStore('clients', () => {
  const clients = ref<Client[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const tags = ref<Tag[]>([])
  const groups = ref<Group[]>([])

  const onlineCount = computed(() => clients.value.filter(c => c.status === 'online').length)

  async function fetchClients(params?: Record<string, any>) {
    loading.value = true
    try {
      const res: PaginatedResponse<Client> = await clientsApi.getClients({
        page: page.value,
        page_size: pageSize.value,
        ...params,
      })
      clients.value = res.items
      total.value = res.total
    } catch {
      console.error('Failed to fetch clients')
    } finally {
      loading.value = false
    }
  }

  async function fetchTags() {
    try {
      tags.value = await getTags()
    } catch {
      console.error('Failed to fetch tags')
    }
  }

  async function fetchGroups() {
    try {
      groups.value = await getGroups()
    } catch {
      console.error('Failed to fetch groups')
    }
  }

  async function updateClient(id: number, data: Partial<Client>) {
    const updated = await clientsApi.updateClient(id, data)
    const idx = clients.value.findIndex(c => c.id === id)
    if (idx >= 0) clients.value[idx] = updated
  }

  async function deleteClient(id: number) {
    await clientsApi.deleteClient(id)
    clients.value = clients.value.filter(c => c.id !== id)
  }

  async function sendCommand(id: number, command: string, payload?: Record<string, any>) {
    await clientsApi.sendCommand(id, command, payload)
  }

  return {
    clients, total, page, pageSize, loading, tags, groups, onlineCount,
    fetchClients, fetchTags, fetchGroups, updateClient, deleteClient, sendCommand,
  }
})
