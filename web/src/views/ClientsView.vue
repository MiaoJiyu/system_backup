<template>
  <div class="space-y-4 animate-fade-in">
    <div class="card">
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <div class="flex items-center gap-2 flex-1 min-w-[200px]">
          <el-input v-model="searchQuery" placeholder="搜索 UUID、IP..." size="default" class="max-w-xs" clearable @input="onSearch">
            <template #prefix><Search class="w-4 h-4 text-gray-400" /></template>
          </el-input>
          <el-select v-model="filterGroup" placeholder="分组筛选" size="default" clearable class="w-36" @change="onSearch">
            <el-option v-for="g in store.groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <el-select v-model="filterTag" placeholder="标签筛选" size="default" clearable class="w-36" @change="onSearch">
            <el-option v-for="t in store.tags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </div>
        <div class="flex gap-2 ml-auto">
          <el-button type="danger" size="default" :disabled="selectedIds.length === 0" @click="handleBatchDelete">
            批量删除
          </el-button>
          <el-button type="primary" size="default" @click="refresh">
            <RefreshCw class="w-4 h-4" /> 刷新
          </el-button>
        </div>
      </div>

      <el-table
        :data="store.clients"
        style="width: 100%"
        size="default"
        stripe
        @selection-change="onSelectionChange"
        @row-click="onRowClick"
        v-loading="store.loading"
        class="cursor-pointer"
      >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="uuid" label="UUID" min-width="140">
          <template #default="{ row }">
            <span class="font-mono text-xs">{{ row.uuid?.substring(0, 8) }}...</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="130" />
        <el-table-column label="分组" width="100">
          <template #default="{ row }">
            <span class="text-sm text-gray-500">{{ row.group?.name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="120">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <span v-for="(tag, i) in (row.tags || [])" :key="i" class="badge badge-info">{{ tag }}</span>
              <span v-if="!row.tags?.length" class="text-gray-400 text-xs">-</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <span :class="['inline-flex items-center gap-1.5 text-sm', row.status === 'online' ? 'text-green-600' : 'text-gray-400']">
              <span :class="['w-2 h-2 rounded-full', row.status === 'online' ? 'bg-green-500 animate-pulse-dot' : 'bg-gray-400']" />
              {{ row.status === 'online' ? '在线' : '离线' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="client_version" label="版本" width="90">
          <template #default="{ row }">
            <span class="text-xs">{{ row.client_version || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后在线" min-width="150">
          <template #default="{ row }">
            <span class="text-sm text-gray-500">{{ row.last_seen || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="$router.push(`/clients/${row.id}`)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-between items-center mt-4">
        <span class="text-sm text-gray-500">共 {{ store.total }} 台客户端，{{ store.onlineCount }} 台在线</span>
        <el-pagination
          v-model:current-page="store.page"
          v-model:page-size="store.pageSize"
          :total="store.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          small
          @change="refresh"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, RefreshCw } from 'lucide-vue-next'
import { useClientsStore } from '@/stores/clients'
import type { Client } from '@/types'

const router = useRouter()
const store = useClientsStore()
const searchQuery = ref('')
const filterGroup = ref<number | null>(null)
const filterTag = ref<number | null>(null)
const selectedIds = ref<number[]>([])

function onSearch() {
  store.page = 1
  refresh()
}

function onSelectionChange(rows: Client[]) {
  selectedIds.value = rows.map(r => r.id)
}

function onRowClick(row: Client) {
  router.push(`/clients/${row.id}`)
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个客户端吗？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  for (const id of selectedIds.value) {
    await store.deleteClient(id)
  }
  ElMessage.success('删除成功')
  selectedIds.value = []
  refresh()
}

async function refresh() {
  const params: Record<string, any> = {}
  if (searchQuery.value) params.search = searchQuery.value
  if (filterGroup.value) params.group_id = filterGroup.value
  if (filterTag.value) params.tag_id = filterTag.value
  await store.fetchClients(params)
}

onMounted(async () => {
  await Promise.all([store.fetchClients(), store.fetchTags(), store.fetchGroups()])
})
</script>
