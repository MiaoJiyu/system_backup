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

      <el-divider />
      <h4 class="text-sm font-medium text-gray-700 mb-3">策略分配</h4>
      <div class="flex items-center gap-2 mb-3">
        <el-select v-model="assignType" class="w-24" size="small">
          <el-option label="分组" value="group" />
          <el-option label="标签" value="tag" />
          <el-option label="客户端" value="client" />
        </el-select>
        <el-select v-model="assignTargetId" class="w-48" size="small" filterable placeholder="选择目标">
          <el-option v-for="t in assignOptions" :key="t.id" :label="t.label" :value="t.id" />
        </el-select>
        <el-button size="small" type="primary" @click="handleAssign" :loading="assigning">分配</el-button>
      </div>
      <div v-if="assignments.length" class="space-y-1 max-h-60 overflow-y-auto">
        <div v-for="a in assignments" :key="a.id" class="flex items-center justify-between px-3 py-1.5 bg-gray-50 rounded text-sm">
          <span class="text-gray-600">{{ a.label }}</span>
          <div class="flex gap-1">
            <el-button link type="success" size="small" @click="handleBackupAssign(a)">执行</el-button>
            <el-button link type="danger" size="small" @click="handleRemoveAssign(a)">移除</el-button>
          </div>
        </div>
      </div>
      <p v-else class="text-sm text-gray-400">暂无分配</p>
    </div>
    <div v-else class="card flex-1 flex items-center justify-center text-gray-400">请选择左侧策略模板</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { getPolicies, createPolicy, updatePolicy, deletePolicy as delPolicy, assignPolicy, getAssignments, removeAssignment } from '@/api/policies'
import { getStorages } from '@/api/storages'
import { getGroups } from '@/api/groups'
import { getClients, sendCommand } from '@/api/clients'
import type { PolicyTemplate, Storage } from '@/types'

const policies = ref<PolicyTemplate[]>([])
const storages = ref<Storage[]>([])
const selected = ref<PolicyTemplate | null>(null)
const saving = ref(false)
const deleting = ref(false)
const assigning = ref(false)
const assignType = ref('group')
const assignTargetId = ref<number | null>(null)
const assignOptions = ref<{ id: number; label: string }[]>([])
const assignments = ref<any[]>([])

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
  loadAssignments()
  loadAssignOptions()
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

async function loadAssignments() {
  if (!selected.value) return
  try {
    const all = await getAssignments()
    const pid = selected.value.id
    assignments.value = [
      ...(all.group_assignments || []).filter((a: any) => a.policy_id === pid).map((a: any) => ({ ...a, type: 'group', label: `分组: ${a.group}` })),
      ...(all.tag_assignments || []).filter((a: any) => a.policy_id === pid).map((a: any) => ({ ...a, type: 'tag', label: `标签: ${a.tag}` })),
      ...(all.client_overrides || []).filter((a: any) => a.policy_id === pid).map((a: any) => ({ ...a, type: 'client', label: `客户端: ${a.client_uuid}` })),
    ]
  } catch { assignments.value = [] }
}

async function loadAssignOptions() {
  try {
    if (assignType.value === 'group') {
      const gs = await getGroups()
      assignOptions.value = gs.map((g: any) => ({ id: g.id, label: g.name }))
    } else if (assignType.value === 'client') {
      const cs = await getClients({ page_size: 200 })
      assignOptions.value = cs.items.map((c: any) => ({ id: c.id, label: `${c.uuid?.substring(0, 8)}... (${c.ip_address || '?'})` }))
    } else {
      assignOptions.value = []
    }
  } catch { assignOptions.value = [] }
}

async function handleAssign() {
  if (!selected.value || !assignTargetId.value) {
    ElMessage.warning('请选择目标')
    return
  }
  assigning.value = true
  try {
    const payload: any = { policy_template_id: selected.value.id }
    if (assignType.value === 'group') payload.group_id = assignTargetId.value
    else if (assignType.value === 'tag') payload.tag_id = assignTargetId.value
    else payload.client_id = assignTargetId.value
    await assignPolicy(payload)
    ElMessage.success('策略已分配')
    assignTargetId.value = null
    await loadAssignments()
  } catch { ElMessage.error('分配失败') }
  finally { assigning.value = false }
}

async function handleRemoveAssign(a: any) {
  try { await ElMessageBox.confirm('确定移除此分配？', '确认', { type: 'warning' }) } catch { return }
  try {
    await removeAssignment(a.type, a.id)
    ElMessage.success('已移除')
    await loadAssignments()
  } catch { ElMessage.error('移除失败') }
}

async function handleBackupAssign(a: any) {
  // Trigger manual backup for a specific assigned client
  if (a.type === 'client' && a.client_id) {
    try {
      await sendCommand(a.client_id, 'start_backup')
      ElMessage.success('手动备份指令已发送')
    } catch { ElMessage.error('发送失败，请确认客户端在线') }
  } else if (a.type === 'group' && a.group_id) {
    // For groups, send to all clients in that group
    try {
      const res = await getClients({ group_id: a.group_id, page_size: 500 })
      let sent = 0
      for (const c of res.items) {
        try { await sendCommand(c.id, 'start_backup'); sent++ } catch { /* skip offline */ }
      }
      ElMessage.success(`已向 ${sent}/${res.items.length} 个客户端发送备份指令`)
    } catch { ElMessage.error('获取分组客户端失败') }
  } else {
    ElMessage.warning('此分配类型暂不支持批量执行')
  }
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
