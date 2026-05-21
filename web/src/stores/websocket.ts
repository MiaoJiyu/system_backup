import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WSMessage, ClientLog } from '@/types'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref<WebSocket | null>(null)
  const connected = ref(false)
  const logMessages = ref<ClientLog[]>([])
  const maxLogs = 500

  function connect(clientId?: number) {
    disconnect()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = clientId
      ? `${protocol}//${window.location.host}/api/v1/ws/clients/${clientId}/logs`
      : `${protocol}//${window.location.host}/api/v1/ws`

    const ws = new WebSocket(url)
    ws.onopen = () => {
      connected.value = true
    }
    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch {
        console.error('Failed to parse WS message')
      }
    }
    ws.onclose = () => {
      connected.value = false
      setTimeout(() => connect(clientId), 3000)
    }
    ws.onerror = () => {
      ws.close()
    }
    socket.value = ws
  }

  function handleMessage(msg: WSMessage) {
    switch (msg.type) {
      case 'log':
      case 'client_log': {
        if (msg.payload) {
          const log = Array.isArray(msg.payload) ? msg.payload : [msg.payload]
          logMessages.value = [...logMessages.value, ...log].slice(-maxLogs)
        }
        break
      }
    }
  }

  function disconnect() {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    connected.value = false
  }

  function clearLogs() {
    logMessages.value = []
  }

  function sendMessage(msg: WSMessage) {
    if (socket.value && connected.value) {
      socket.value.send(JSON.stringify(msg))
    }
  }

  return { connected, logMessages, connect, disconnect, clearLogs, sendMessage }
})
