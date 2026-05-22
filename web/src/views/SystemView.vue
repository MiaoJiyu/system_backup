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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditUser(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" size="small" class="mt-4" @click="showCreateUser = true">
        <Plus class="w-3 h-3" /> 创建用户
      </el-button>
    </div>

    <!-- Change password (any logged-in user) -->
    <div class="card">
      <h3 class="font-medium text-gray-800 mb-4">修改密码</h3>
      <el-form :model="pwdForm" label-width="100px" class="max-w-sm">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword" :loading="pwdLoading">修改密码</el-button>
        </el-form-item>
      </el-form>
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

    <el-dialog v-model="showEditDialog" title="编辑用户" width="400px">
      <el-form :model="editForm">
        <el-form-item label="用户名"><el-input v-model="editForm.username" /></el-form-item>
        <el-form-item label="新密码（留空不修改）">
          <el-input v-model="editForm.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEditUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { getSystemStatus } from '@/api/system'
import { register, changePassword, getUsers, updateUser, deleteUser } from '@/api/auth'
import { getClients } from '@/api/clients'
import type { SystemStatus, User } from '@/types'

const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)
const status = ref<SystemStatus | null>(null)
const dbConnected = ref(true)
const users = ref<User[]>([])
const userLoading = ref(false)
const showCreateUser = ref(false)
const showEditDialog = ref(false)
const pwdLoading = ref(false)

const newUser = ref({ username: '', password: '', role: 'user' })
const editForm = ref({ id: 0, username: '', password: '', role: 'user' })
const pwdForm = ref({ old_password: '', new_password: '' })

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
    await loadUsers()
  } catch { ElMessage.error('创建失败') }
}

function showEditUser(row: User) {
  editForm.value = { id: row.id, username: row.username, password: '', role: row.role }
  showEditDialog.value = true
}

async function handleEditUser() {
  try {
    const payload: any = { username: editForm.value.username, role: editForm.value.role }
    if (editForm.value.password) payload.password = editForm.value.password
    await updateUser(editForm.value.id, payload)
    ElMessage.success('已更新')
    showEditDialog.value = false
    await loadUsers()
  } catch { ElMessage.error('更新失败') }
}

async function handleDeleteUser(row: User) {
  try { await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteUser(row.id)
    ElMessage.success('已删除')
    await loadUsers()
  } catch { ElMessage.error('删除失败') }
}

async function handleChangePassword() {
  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  pwdLoading.value = true
  try {
    await changePassword(pwdForm.value)
    ElMessage.success('密码已修改')
    pwdForm.value = { old_password: '', new_password: '' }
  } catch { ElMessage.error('修改失败') }
  finally { pwdLoading.value = false }
}

async function loadUsers() {
  if (!isAdmin.value) return
  userLoading.value = true
  try {
    users.value = await getUsers()
  } catch { users.value = [] }
  finally { userLoading.value = false }
}

onMounted(async () => {
  try {
    status.value = await getSystemStatus()
    const res = await getClients({ page_size: 1 })
    if (res) dbConnected.value = true
    await loadUsers()
  } catch { dbConnected.value = false }
})
</script>
