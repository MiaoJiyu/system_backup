<template>
  <div class="flex gap-4 h-[calc(100vh-160px)] animate-fade-in">
    <div class="card w-72 flex-shrink-0 overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-800">分组树</h3>
        <el-button size="small" type="primary" @click="addGroup(null)"><Plus class="w-3 h-3" /></el-button>
      </div>
      <el-tree
        :data="treeData"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        default-expand-all
        highlight-current
        @node-click="onSelect"
      >
        <template #default="{ data }">
          <span class="flex items-center gap-2 text-sm">
            <FolderTree class="w-4 h-4 text-primary" />
            <span>{{ data.name }}</span>
            <span class="text-xs text-gray-400">({{ data.clients?.length || 0 }})</span>
          </span>
        </template>
      </el-tree>
    </div>

    <div class="card flex-1">
      <div v-if="selectedGroup">
        <el-form :model="form" label-width="80px" @submit.prevent="handleSave">
          <el-form-item label="名称">
            <el-input v-model="form.name" class="max-w-sm" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="2" class="max-w-sm" />
          </el-form-item>
          <el-form-item label="父分组">
            <el-select v-model="form.parent_id" clearable placeholder="无（根分组）" class="max-w-sm">
              <el-option v-for="g in flatGroups" :key="g.id" :label="g.name" :value="g.id"
                :disabled="g.id === selectedGroup.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            <el-button type="danger" @click="handleDelete" :disabled="!selectedGroup">删除</el-button>
          </el-form-item>
        </el-form>

        <el-divider />
        <h4 class="text-sm font-medium text-gray-700 mb-3">已绑定策略</h4>
        <div class="flex flex-wrap gap-2" v-if="boundPolicies.length">
          <span v-for="p in boundPolicies" :key="p.id" class="badge badge-info">{{ p.name }}</span>
        </div>
        <p v-else class="text-sm text-gray-400">暂无绑定策略</p>

        <el-divider />
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-sm font-medium text-gray-700">组内客户端 ({{ groupClients.length }})</h4>
          <el-button size="small" type="primary" @click="showAddClientsDialog = true" :disabled="!selectedGroup">
            <Plus class="w-3 h-3" /> 添加客户端
          </el-button>
        </div>
        <div v-if="groupClients.length" class="space-y-1 max-h-60 overflow-y-auto">
          <div v-for="c in groupClients" :key="c.id" class="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg text-sm">
            <span class="font-mono text-xs text-gray-600">{{ c.uuid?.substring(0, 12) }}...</span>
            <el-button link type="danger" size="small" @click="handleRemoveClient(c)">移除</el-button>
          </div>
        </div>
        <p v-else class="text-sm text-gray-400">暂无客户端</p>
      </div>
      <div v-else class="text-center text-gray-400 pt-20">请选择左侧分组查看详情</div>

    <!-- Add clients dialog -->
    <el-dialog v-model="showAddClientsDialog" title="添加客户端到分组" width="550px">
      <el-transfer
        v-model="selectedClientIds"
        :data="availableClientOptions"
        :titles="['可选客户端', '已选择']"
        filterable
      />
      <template #footer>
        <el-button @click="showAddClientsDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddClients" :loading="addingClients">确定</el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, FolderTree } from 'lucide-vue-next'
import { getGroups, createGroup, updateGroup, deleteGroup, getGroupClients, addClientsToGroup, removeClientFromGroup } from '@/api/groups'
import { getClients } from '@/api/clients'
import { getAssignments } from '@/api/policies'
import type { Group, Client } from '@/types'

const treeData = ref<Group[]>([])
const selectedGroup = ref<Group | null>(null)
const boundPolicies = ref<any[]>([])
const saving = ref(false)
const form = ref({ name: '', description: '', parent_id: null as number | null })
const groupClients = ref<Client[]>([])
const showAddClientsDialog = ref(false)
const selectedClientIds = ref<number[]>([])
const availableClientOptions = ref<{ key: number; label: string }[]>([])
const addingClients = ref(false)

const flatGroups = computed(() => {
  const result: Group[] = []
  function walk(list: Group[]) {
    for (const g of list) {
      result.push(g)
      if (g.children) walk(g.children)
    }
  }
  walk(treeData.value)
  return result
})

function buildTree(groups: Group[]): Group[] {
  const map = new Map<number, Group>()
  const roots: Group[] = []
  for (const g of groups) {
    map.set(g.id, { ...g, children: [] })
  }
  for (const g of map.values()) {
    if (g.parent_id && map.has(g.parent_id)) {
      map.get(g.parent_id)!.children!.push(g)
    } else {
      roots.push(g)
    }
  }
  return roots
}

async function onSelect(data: Group) {
  selectedGroup.value = data
  form.value = { name: data.name, description: data.description || '', parent_id: data.parent_id }
  await Promise.all([loadGroupClients(), loadBoundPolicies()])
}

async function loadBoundPolicies() {
  if (!selectedGroup.value) return
  try {
    const all = await getAssignments()
    boundPolicies.value = (all.group_assignments || [])
      .filter((a: any) => a.group_id === selectedGroup.value!.id)
      .map((a: any) => ({ id: a.id, name: a.policy }))
  } catch { boundPolicies.value = [] }
}

async function loadGroupClients() {
  if (!selectedGroup.value) return
  try {
    groupClients.value = await getGroupClients(selectedGroup.value.id)
  } catch { groupClients.value = [] }
}

async function handleRemoveClient(c: Client) {
  if (!selectedGroup.value) return
  try {
    await removeClientFromGroup(selectedGroup.value.id, c.id)
    ElMessage.success('已移除')
    await loadGroupClients()
  } catch { ElMessage.error('移除失败') }
}

function onShowAddClientsDialog() {
  // Load available clients for transfer
  getClients({ page_size: 200 }).then(res => {
    availableClientOptions.value = res.items
      .filter((c: Client) => c.group_id !== selectedGroup.value?.id)
      .map((c: Client) => ({ key: c.id, label: `${c.uuid?.substring(0, 8)}... (${c.ip_address || 'unknown'})` }))
  }).catch(() => {})
}

async function confirmAddClients() {
  if (!selectedGroup.value || selectedClientIds.value.length === 0) {
    ElMessage.warning('请选择客户端')
    return
  }
  addingClients.value = true
  try {
    await addClientsToGroup(selectedGroup.value.id, selectedClientIds.value)
    ElMessage.success('客户端已添加')
    showAddClientsDialog.value = false
    selectedClientIds.value = []
    await loadGroupClients()
  } catch { ElMessage.error('添加失败') }
  finally { addingClients.value = false }
}

async function addGroup(parentId: number | null) {
  try {
    const name = prompt('请输入分组名称')
    if (!name) return
    await createGroup({ name, parent_id: parentId })
    await fetchGroups()
    ElMessage.success('分组已创建')
  } catch { ElMessage.error('创建失败') }
}

async function handleSave() {
  if (!selectedGroup.value) return
  saving.value = true
  try {
    await updateGroup(selectedGroup.value.id, form.value)
    ElMessage.success('已保存')
    fetchGroups()
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

async function handleDelete() {
  if (!selectedGroup.value) return
  try {
    await ElMessageBox.confirm('确定要删除此分组吗？', '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await deleteGroup(selectedGroup.value.id)
    selectedGroup.value = null
    await fetchGroups()
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败，请确保分组下无客户端') }
}

async function fetchGroups() {
  try {
    const data = await getGroups()
    treeData.value = buildTree(data)
  } catch { console.error('Failed to fetch groups') }
}

watch(showAddClientsDialog, (val) => {
  if (val) onShowAddClientsDialog()
})

onMounted(fetchGroups)
</script>
