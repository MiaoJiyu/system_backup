<template>
  <div class="flex gap-4 h-[calc(100vh-160px)] animate-fade-in">
    <div class="card w-64 flex-shrink-0 overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-800">策略模板</h3>
        <el-button size="small" type="primary" @click="addPolicy"><Plus class="w-3 h-3" /></el-button>
      </div>
      <div class="space-y-1">
        <div
          v-for="p in policies"
          :key="p.id"
          @click="selectPolicy(p)"
          :class="['px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm', selected?.id === p.id ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-gray-50 text-gray-700']"
        >
          {{ p.name }}
        </div>
      </div>
    </div>

    <div class="card flex-1 overflow-y-auto" v-if="selected">
      <el-form :model="form" label-width="110px" size="default">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="备份目录">
          <el-select v-model="form.backup_directories" multiple filterable allow-create placeholder="输入路径后回车添加" class="w-full" />
        </el-form-item>
        <el-form-item label="备份U盘"><el-switch v-model="form.backup_usb" /></el-form-item>
        <el-form-item label="增量备份"><el-switch v-model="form.incremental" /></el-form-item>
        <el-form-item label="定时类型">
          <el-select v-model="form.schedule_type" class="w-40">
            <el-option label="手动" value="manual" />
            <el-option label="Cron表达式" value="cron" />
            <el-option label="间隔" value="interval" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'cron'" label="Cron表达式">
          <el-input v-model="form.schedule_config.cron" placeholder="0 */6 * * *" class="max-w-xs" />
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'interval'" label="间隔(秒)">
          <el-input-number v-model="form.schedule_config.interval_seconds" :min="60" class="max-w-xs" />
        </el-form-item>
        <el-form-item label="存储目标">
          <el-select v-model="form.upload_storage_id" clearable class="w-60">
            <el-option v-for="s in storages" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="加密"><el-switch v-model="form.encryption_enabled" /></el-form-item>
        <el-form-item label="压缩"><el-switch v-model="form.compression_enabled" /></el-form-item>
        <el-form-item label="更新策略">
          <el-select v-model="form.version_update_policy" class="w-40">
            <el-option label="强制更新" value="force" />
            <el-option label="任务后更新" value="after_task" />
            <el-option label="空闲时更新" value="idle" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="savePolicy" :loading="saving">保存</el-button>
          <el-button type="danger" @click="deletePolicy" :loading="deleting">删除</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div v-else class="card flex-1 flex items-center justify-center text-gray-400">请选择左侧策略模板</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { getPolicies, createPolicy, updatePolicy, deletePolicy as delPolicy } from '@/api/policies'
import { getStorages } from '@/api/storages'
import type { PolicyTemplate, Storage } from '@/types'

const policies = ref<PolicyTemplate[]>([])
const storages = ref<Storage[]>([])
const selected = ref<PolicyTemplate | null>(null)
const saving = ref(false)
const deleting = ref(false)

const form = reactive<Record<string, any>>({
  name: '', description: '', backup_directories: [], backup_usb: true,
  incremental: true, backup_meta_log: true, schedule_type: 'manual',
  schedule_config: {}, upload_storage_id: null, server_address: '',
  server_port: null, encryption_enabled: true, compression_enabled: true,
  version_update_policy: 'after_task',
})

function selectPolicy(p: PolicyTemplate) {
  selected.value = p
  Object.assign(form, {
    name: p.name, description: p.description || '', backup_directories: p.backup_directories || [],
    backup_usb: p.backup_usb, incremental: p.incremental, backup_meta_log: p.backup_meta_log,
    schedule_type: p.schedule_type, schedule_config: p.schedule_config || {},
    upload_storage_id: p.upload_storage_id, server_address: p.server_address || '',
    server_port: p.server_port, encryption_enabled: p.encryption_enabled,
    compression_enabled: p.compression_enabled, version_update_policy: p.version_update_policy,
  })
}

async function addPolicy() {
  const name = prompt('请输入策略名称')
  if (!name) return
  try {
    const p = await createPolicy({ name } as any)
    policies.value.push(p)
    selectPolicy(p)
    ElMessage.success('策略已创建')
  } catch { ElMessage.error('创建失败') }
}

async function savePolicy() {
  if (!selected.value) return
  saving.value = true
  try {
    await updatePolicy(selected.value.id, { ...form })
    Object.assign(selected.value, { ...form })
    ElMessage.success('已保存')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

async function deletePolicy() {
  if (!selected.value) return
  try { await ElMessageBox.confirm('确定删除此策略？', '确认', { type: 'warning' }) } catch { return }
  deleting.value = true
  try {
    await delPolicy(selected.value.id)
    policies.value = policies.value.filter(p => p.id !== selected.value!.id)
    selected.value = null
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
  finally { deleting.value = false }
}

onMounted(async () => {
  try {
    const [ps, ss] = await Promise.all([getPolicies(), getStorages()])
    policies.value = ps.items
    storages.value = ss
  } catch { console.error('Failed to load') }
})
</script>
