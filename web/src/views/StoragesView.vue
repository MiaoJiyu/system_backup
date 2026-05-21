<template>
  <div class="space-y-4 animate-fade-in">
    <div class="flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-800">存储后端管理</h2>
      <el-button type="primary" @click="showDialog = true"><Plus class="w-4 h-4" /> 新增</el-button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="s in storages" :key="s.id" class="card hover:shadow-lg transition-shadow cursor-pointer" @click="editStorage(s)">
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', typeIconBg(s.type)]">
              <HardDrive class="w-5 h-5 text-white" />
            </div>
            <div>
              <p class="font-medium text-gray-800">{{ s.name }}</p>
              <p class="text-xs text-gray-400">{{ typeLabel(s.type) }}</p>
            </div>
          </div>
          <el-switch v-model="s.enabled" size="small" @click.stop @change="toggleEnabled(s)" />
        </div>
        <div class="text-xs text-gray-500 space-y-1">
          <p v-if="s.type === 'local'">路径: {{ s.config?.path || '-' }}</p>
          <p v-if="s.type === 's3'">端点: {{ s.config?.endpoint || '-' }}</p>
          <p v-if="s.type === 'sftp'">主机: {{ s.config?.host || '-' }}:{{ s.config?.port || 22 }}</p>
        </div>
      </div>

      <div v-if="storages.length === 0" class="card col-span-full text-center py-16 text-gray-400">
        <HardDrive class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>暂无存储后端配置</p>
      </div>
    </div>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑存储后端' : '新增存储后端'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio value="local">本地</el-radio>
            <el-radio value="s3">S3</el-radio>
            <el-radio value="sftp">SFTP</el-radio>
          </el-radio-group>
        </el-form-item>
        <template v-if="form.type === 'local'">
          <el-form-item label="路径"><el-input v-model="form.config.path" placeholder="/mnt/backup" /></el-form-item>
        </template>
        <template v-if="form.type === 's3'">
          <el-form-item label="端点"><el-input v-model="form.config.endpoint" placeholder="https://s3.example.com" /></el-form-item>
          <el-form-item label="Bucket"><el-input v-model="form.config.bucket" /></el-form-item>
          <el-form-item label="Region"><el-input v-model="form.config.region" placeholder="us-east-1" /></el-form-item>
          <el-form-item label="AccessKey"><el-input v-model="form.config.access_key" /></el-form-item>
          <el-form-item label="SecretKey"><el-input v-model="form.config.secret_key" type="password" show-password /></el-form-item>
        </template>
        <template v-if="form.type === 'sftp'">
          <el-form-item label="主机"><el-input v-model="form.config.host" /></el-form-item>
          <el-form-item label="端口"><el-input-number v-model="form.config.port" :min="1" :max="65535" /></el-form-item>
          <el-form-item label="用户名"><el-input v-model="form.config.username" /></el-form-item>
          <el-form-item label="认证方式">
            <el-select v-model="form.config.auth_type" class="w-full">
              <el-option label="密码" value="password" />
              <el-option label="密钥" value="key" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.config.auth_type === 'password'" label="密码">
            <el-input v-model="form.config.password" type="password" show-password />
          </el-form-item>
          <el-form-item label="路径前缀"><el-input v-model="form.config.path_prefix" placeholder="/uploads/" /></el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button v-if="editingId" type="danger" @click="handleDelete">删除</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, HardDrive } from 'lucide-vue-next'
import { getStorages, createStorage, updateStorage, deleteStorage } from '@/api/storages'
import type { Storage } from '@/types'

const storages = ref<Storage[]>([])
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const defaultForm = () => ({
  name: '', type: 'local' as string,
  config: { path: '', endpoint: '', bucket: '', region: '', access_key: '', secret_key: '', host: '', port: 22, username: '', auth_type: 'password', password: '', path_prefix: '/uploads/' },
})

const form = reactive<Record<string, any>>({ ...defaultForm() })

function typeLabel(t: string) { return t === 'local' ? '本地存储' : t === 's3' ? 'S3 对象存储' : 'SFTP 服务器' }
function typeIconBg(t: string) { return t === 'local' ? 'bg-green-500' : t === 's3' ? 'bg-blue-500' : 'bg-purple-500' }

function editStorage(s: Storage) {
  editingId.value = s.id
  form.name = s.name
  form.type = s.type
  form.config = { ...form.config, ...s.config }
  showDialog.value = true
}

async function handleSave() {
  if (!form.name) { ElMessage.warning('请输入名称'); return }
  saving.value = true
  try {
    if (editingId.value) {
      await updateStorage(editingId.value, { name: form.name, type: form.type as any, config: form.config, enabled: true })
      ElMessage.success('已保存')
    } else {
      await createStorage({ name: form.name, type: form.type as any, config: form.config, enabled: true } as any)
      ElMessage.success('已创建')
    }
    showDialog.value = false
    Object.assign(form, defaultForm())
    editingId.value = null
    storages.value = await getStorages()
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

async function handleDelete() {
  if (!editingId.value) return
  try { await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteStorage(editingId.value)
    showDialog.value = false
    editingId.value = null
    Object.assign(form, defaultForm())
    storages.value = await getStorages()
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}

async function toggleEnabled(s: Storage) {
  try {
    await updateStorage(s.id, { enabled: s.enabled } as any)
  } catch { s.enabled = !s.enabled }
}

onMounted(async () => {
  try { storages.value = await getStorages() } catch { console.error('Failed to load storages') }
})
</script>
