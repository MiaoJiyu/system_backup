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
          <div v-if="editingPolicy" class="space-y-4">
            <el-form :model="policyForm" label-width="120px" size="default">
              <el-form-item label="备份目录">
                <el-select v-model="policyForm.backup_directories" multiple filterable allow-create placeholder="输入路径后回车添加" class="w-full" />
              </el-form-item>
              <el-form-item label="备份U盘"><el-switch v-model="policyForm.backup_usb" /></el-form-item>
              <el-form-item label="增量备份"><el-switch v-model="policyForm.incremental" /></el-form-item>
              <el-form-item label="定时类型">
                <el-select v-model="policyForm.schedule_type" class="w-40">
                  <el-option label="手动" value="manual" />
                  <el-option label="Cron表达式" value="cron" />
                  <el-option label="间隔" value="interval" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="policyForm.schedule_type === 'cron'" label="Cron表达式">
                <el-input v-model="policyForm.schedule_config.cron" placeholder="0 */6 * * *" class="max-w-xs" />
              </el-form-item>
              <el-form-item v-if="policyForm.schedule_type === 'interval'" label="间隔(秒)">
                <el-input-number v-model="policyForm.schedule_config.interval_seconds" :min="60" class="max-w-xs" />
              </el-form-item>
              <el-form-item label="加密"><el-switch v-model="policyForm.encryption_enabled" /></el-form-item>
              <el-form-item label="压缩"><el-switch v-model="policyForm.compression_enabled" /></el-form-item>
              <el-form-item>
                <el-button type="primary" @click="savePolicy" :loading="savingPolicy">保存并推送</el-button>
                <el-button @click="editingPolicy = false">取消</el-button>
              </el-form-item>
            </el-form>
          </div>
          <div v-else>
            <el-button type="primary" size="small" class="mb-3" @click="startEditPolicy">编辑策略</el-button>
            <pre class="bg-gray-50 rounded-lg p-4 text-sm overflow-auto max-h-80">{{ JSON.stringify(effectivePolicy, null, 2) || '暂无策略' }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { getClient, getClientBackups, getEffectivePolicy, pushClientConfig } from '@/api/clients'
import { useWebSocketStore } from '@/stores/websocket'
import type { Client, BackupRecord } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const ws = useWebSocketStore()
const client = ref<Client | null>(null)
const backups = ref<BackupRecord[]>([])
const effectivePolicy = ref<Record<string, any> | null>(null)
const loading = ref(true)
const activeTab = ref('logs')
const logContainer = ref<HTMLElement>()
const editingPolicy = ref(false)
const savingPolicy = ref(false)
const policyForm = reactive<Record<string, any>>({
  backup_directories: [], backup_usb: true, incremental: true,
  schedule_type: 'manual', schedule_config: {}, encryption_enabled: true,
  compression_enabled: true,
})

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

function startEditPolicy() {
  if (effectivePolicy.value) {
    Object.assign(policyForm, {
      backup_directories: effectivePolicy.value.backup_directories || [],
      backup_usb: effectivePolicy.value.backup_usb ?? true,
      incremental: effectivePolicy.value.incremental ?? true,
      schedule_type: effectivePolicy.value.schedule_type || 'manual',
      schedule_config: effectivePolicy.value.schedule_config || {},
      encryption_enabled: effectivePolicy.value.encryption_enabled ?? true,
      compression_enabled: effectivePolicy.value.compression_enabled ?? true,
    })
  }
  editingPolicy.value = true
}

async function savePolicy() {
  if (!client.value) return
  savingPolicy.value = true
  try {
    const res = await pushClientConfig(client.value.id, { config: { ...policyForm } })
    effectivePolicy.value = res.effective_policy
    editingPolicy.value = false
    ElMessage.success('配置已保存并推送到客户端')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingPolicy.value = false
  }
}
</script>
