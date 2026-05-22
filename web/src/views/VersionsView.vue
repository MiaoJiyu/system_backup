<template>
  <div class="space-y-4 animate-fade-in">
    <div class="flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-800">客户端版本管理</h2>
      <el-upload :show-file-list="false" :http-request="uploadFile" accept=".exe,.zip,.msi">
        <el-button type="primary"><Upload class="w-4 h-4" /> 上传新版本</el-button>
      </el-upload>
    </div>

    <div class="card">
      <el-table :data="versions" style="width: 100%" stripe v-loading="loading">
        <el-table-column prop="version" label="版本号" width="120">
          <template #default="{ row }"><span class="font-mono text-sm font-medium">{{ row.version }}</span></template>
        </el-table-column>
        <el-table-column prop="file_name" label="文件名" min-width="180" />
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column prop="changelog" label="变更日志" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.changelog" placement="top" :show-after="300">
              <span class="text-sm text-gray-600 truncate block max-w-[200px]">{{ row.changelog || '-' }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handlePush(row)">推送更新</el-button>
            <el-button link type="success" size="small" @click="downloadVersion(row)">下载</el-button>
            <el-button link type="primary" size="small" @click="editMirror(row)">镜像</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="pushDialogVisible" title="推送更新" width="500px">
      <p class="mb-4 text-sm text-gray-600">选择要推送的目标客户端（版本 {{ pushTarget?.version }}）</p>
      <el-transfer v-model="pushClientIds" :data="pushClientOptions" :titles="['可用客户端', '已选择']" />
      <template #footer>
        <el-button @click="pushDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPush">确认推送</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="mirrorDialogVisible" title="编辑镜像地址" width="500px">
      <el-form :model="mirrorForm">
        <el-form-item label="主下载地址"><el-input v-model="mirrorForm.download_url" /></el-form-item>
        <el-form-item label="镜像地址"><el-input v-model="mirrorForm.mirror_url" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mirrorDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmMirror">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from 'lucide-vue-next'
import { getVersions, uploadVersion, updateVersion, deleteVersion, pushVersion } from '@/api/versions'
import { getClients } from '@/api/clients'
import type { ClientVersion, Client } from '@/types'

const versions = ref<ClientVersion[]>([])
const loading = ref(false)
const pushDialogVisible = ref(false)
const pushTarget = ref<ClientVersion | null>(null)
const pushClientIds = ref<number[]>([])
const pushClientOptions = ref<{ key: number; label: string }[]>([])
const mirrorDialogVisible = ref(false)
const mirrorForm = ref({ download_url: '', mirror_url: '' })
const mirrorTarget = ref<ClientVersion | null>(null)

function formatSize(bytes: number | null): string {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

async function uploadFile(options: any) {
  const fd = new FormData()
  fd.append('file', options.file)
  fd.append('version', prompt('请输入版本号（如 2.0.1）') || '')
  fd.append('changelog', prompt('请输入变更日志') || '')
  try {
    await uploadVersion(fd)
    ElMessage.success('上传成功')
    await fetchVersions()
  } catch { ElMessage.error('上传失败') }
}

async function handlePush(row: ClientVersion) {
  pushTarget.value = row
  pushClientIds.value = []
  try {
    const res = await getClients({ page_size: 100 })
    pushClientOptions.value = res.items.map((c: Client) => ({ key: c.id, label: `${c.uuid?.substring(0, 8)}... (${c.ip_address || 'unknown'})` }))
  } catch { console.error('Failed to load clients') }
  pushDialogVisible.value = true
}

async function confirmPush() {
  if (!pushTarget.value || pushClientIds.value.length === 0) {
    ElMessage.warning('请选择目标客户端')
    return
  }
  try {
    await pushVersion(pushTarget.value.id, pushClientIds.value)
    ElMessage.success('推送指令已发送')
    pushDialogVisible.value = false
  } catch { ElMessage.error('推送失败') }
}

function editMirror(row: ClientVersion) {
  mirrorTarget.value = row
  mirrorForm.value = { download_url: row.download_url || '', mirror_url: row.mirror_url || '' }
  mirrorDialogVisible.value = true
}

async function confirmMirror() {
  if (!mirrorTarget.value) return
  try {
    await updateVersion(mirrorTarget.value.id, mirrorForm.value)
    ElMessage.success('已更新')
    mirrorDialogVisible.value = false
    await fetchVersions()
  } catch { ElMessage.error('更新失败') }
}

function downloadVersion(row: ClientVersion) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const url = `${baseUrl}/api/v1/versions/download/${row.version}`
  const a = document.createElement('a')
  a.href = url
  a.download = row.file_name || `client-${row.version}.exe`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

async function handleDelete(row: ClientVersion) {
  try { await ElMessageBox.confirm(`确定删除版本 ${row.version}？`, '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteVersion(row.id)
    ElMessage.success('已删除')
    await fetchVersions()
  } catch { ElMessage.error('删除失败') }
}

async function fetchVersions() {
  loading.value = true
  try { const res = await getVersions(); versions.value = res.items } catch { console.error('Failed') }
  finally { loading.value = false }
}

onMounted(fetchVersions)
</script>
