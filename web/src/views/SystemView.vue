<template>
  <div class="space-y-6 animate-fade-in">
    <h2 class="text-lg font-semibold text-gray-800">系统设置</h2>

    <div class="card">
      <h3 class="font-medium text-gray-800 mb-4">数据库状态</h3>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div><span class="text-gray-400">连接状态</span><p :class="dbConnected ? 'text-green-600' : 'text-danger'">{{ dbConnected ? '正常' : '异常' }}</p></div>
        <div><span class="text-gray-400">服务版本</span><p class="text-gray-700">v2.0.0</p></div>
        <div><span class="text-gray-400">在线客户端</span><p class="text-gray-700">{{ status?.online_clients || 0 }}</p></div>
        <div><span class="text-gray-400">总客户端数</span><p class="text-gray-700">{{ status?.total_clients || 0 }}</p></div>
      </div>
    </div>

    <div class="card" v-if="isAdmin">
      <h3 class="font-medium text-gray-800 mb-4">用户管理</h3>
      <el-table :data="users" style="width: 100%" stripe v-loading="userLoading">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <span :class="['badge', row.role === 'admin' ? 'badge-danger' : 'badge-info']">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
      </el-table>
      <el-button type="primary" size="small" class="mt-4" @click="showCreateUser = true">
        <Plus class="w-3 h-3" /> 创建用户
      </el-button>
    </div>

    <div class="card">
      <h3 class="font-medium text-gray-800 mb-4">系统信息</h3>
      <div class="text-sm text-gray-500 space-y-2">
        <p>应用名称: SmartBackup System v2.0</p>
        <p>技术栈: FastAPI + Vue3 + PySide6</p>
        <p>数据库: MySQL / SQLite</p>
        <p>WebSocket: 已启用 (TLS)</p>
      </div>
    </div>

    <el-dialog v-model="showCreateUser" title="创建用户" width="400px">
      <el-form :model="newUser">
        <el-form-item label="用户名"><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newUser.role">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateUser = false">取消</el-button>
        <el-button type="primary" @click="createUser">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { getSystemStatus } from '@/api/system'
import { register } from '@/api/auth'
import { getClients } from '@/api/clients'
import type { SystemStatus, User } from '@/types'

const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)
const status = ref<SystemStatus | null>(null)
const dbConnected = ref(true)
const users = ref<User[]>([])
const userLoading = ref(false)
const showCreateUser = ref(false)

const newUser = ref({ username: '', password: '', role: 'user' })

async function createUser() {
  if (!newUser.value.username || !newUser.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await register(newUser.value)
    ElMessage.success('用户已创建')
    showCreateUser.value = false
    newUser.value = { username: '', password: '', role: 'user' }
  } catch { ElMessage.error('创建失败') }
}

onMounted(async () => {
  try {
    status.value = await getSystemStatus()
    const res = await getClients({ page_size: 1 })
    if (res) dbConnected.value = true
  } catch { dbConnected.value = false }
})
</script>
