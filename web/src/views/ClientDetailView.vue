<template>
  <div class="space-y-4 animate-fade-in" v-loading="loading">
    <div class="flex items-center gap-3 mb-2">
      <el-button size="small" @click="$router.back()" class="!border-gray-300">
        <ArrowLeft class="w-4 h-4" /> 返回
      </el-button>
      <h2 class="text-lg font-semibold text-gray-800">客户端详情</h2>
    </div>

    <div class="card grid grid-cols-2 md:grid-cols-4 gap-4" v-if="client">
      <div><span class="text-xs text-gray-400">UUID</span><p class="font-mono text-sm">{{ client.uuid?.substring(0, 16) }}...</p></div>
      <div><span class="text-xs text-gray-400">IP 地址</span><p class="text-sm">{{ client.ip_address || '-' }}</p></div>
      <div><span class="text-xs text-gray-400">操作系统</span><p class="text-sm">{{ client.os_version || '-' }}</p></div>
      <div><span class="text-xs text-gray-400">客户端版本</span><p class="text-sm">{{ client.client_version || '-' }}</p></div>
      <div><span class="text-xs text-gray-400">状态</span><p>
        <span :class="['inline-flex items-center gap-1', client.status === 'online' ? 'text-green-600' : 'text-gray-400']">
          <span :class="['w-2 h-2 rounded-full', client.status === 'online' ? 'bg-green-500 animate-pulse-dot' : 'bg-gray-400']" />
          {{ client.status === 'online' ? '在线' : '离线' }}
        </span>
      </p></div>
      <div><span class="text-xs text-gray-400">分组</span><p class="text-sm">{{ client.group?.name || '-' }}</p></div>
      <div><span class="text-xs text-gray-400">配置状态</span><p class="text-sm">{{ client.config_status || '-' }}</p></div>
      <div><span class="text-xs text-gray-400">最后在线</span><p class="text-sm">{{ client.last_seen || '-' }}</p></div>
    </div>

    <div class="card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时日志" name="logs">
          <div class="bg-gray-900 rounded-lg p-4 h-80 overflow-y-auto font-mono text-xs" ref="logContainer">
            <div v-if="ws.logMessages.length === 0" class="text-gray-500 text-center pt-20">
              等待日志流...
            </div>
            <div v-for="(log, i) in ws.logMessages" :key="i" class="py-0.5">
              <span class="text-gray-500 mr-2">{{ log.created_at }}</span>
              <span :class="{
                'text-blue-400': log.level === 'INFO',
                'text-yellow-400': log.level === 'WARN',
                'text-red-400': log.level === 'ERROR',
                'text-gray-400': log.level === 'DEBUG',
              }">[{{ log.level }}]</span>
              <span class="text-gray-300 ml-2">{{ log.message }}</span>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="备份历史" name="backups">
          <el-table :data="backups" style="width: 100%" size="small" stripe>
            <el-table-column prop="source_device" label="来源" min-width="140" />
            <el-table-column prop="file_count" label="文件数" width="90" align="center" />
            <el-table-column label="大小" width="110">
              <template #default="{ row }">{{ formatSize(row.total_size) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <span :class="['badge', row.status === 'completed' ? 'badge-success' : row.status === 'failed' ? 'badge-danger' : 'badge-info']">
                  {{ row.status === 'completed' ? '完成' : row.status === 'failed' ? '失败' : '进行中' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="completed_at" label="完成时间" min-width="150" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="生效策略" name="policy">
          <pre class="bg-gray-50 rounded-lg p-4 text-sm overflow-auto max-h-80">{{ JSON.stringify(effectivePolicy, null, 2) || '暂无策略' }}</pre>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { getClient, getClientBackups, getEffectivePolicy } from '@/api/clients'
import { useWebSocketStore } from '@/stores/websocket'
import type { Client, BackupRecord } from '@/types'

const route = useRoute()
const ws = useWebSocketStore()
const client = ref<Client | null>(null)
const backups = ref<BackupRecord[]>([])
const effectivePolicy = ref<Record<string, any> | null>(null)
const loading = ref(true)
const activeTab = ref('logs')
const logContainer = ref<HTMLElement>()

const id = Number(route.params.id)

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

watch(() => ws.logMessages.length, async () => {
  await nextTick()
  if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
})

onMounted(async () => {
  try {
    const [c, b, p] = await Promise.all([
      getClient(id),
      getClientBackups(id, { page: 1, page_size: 50 }),
      getEffectivePolicy(id).catch(() => null),
    ])
    client.value = c
    backups.value = b.items
    effectivePolicy.value = p
  } catch {
    console.error('Failed to load client detail')
  } finally {
    loading.value = false
  }
  ws.clearLogs()
  ws.connect(id)
})

onUnmounted(() => {
  ws.disconnect()
})
</script>
