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
      </div>
      <div v-else class="text-center text-gray-400 pt-20">请选择左侧分组查看详情</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, FolderTree } from 'lucide-vue-next'
import { getGroups, createGroup, updateGroup, deleteGroup } from '@/api/groups'
import type { Group } from '@/types'

const treeData = ref<Group[]>([])
const selectedGroup = ref<Group | null>(null)
const boundPolicies = ref<any[]>([])
const saving = ref(false)
const form = ref({ name: '', description: '', parent_id: null as number | null })

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

function onSelect(data: Group) {
  selectedGroup.value = data
  form.value = { name: data.name, description: data.description || '', parent_id: data.parent_id }
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

onMounted(fetchGroups)
</script>
