<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <aside
      :class="[
        'fixed left-0 top-0 h-full bg-sidebar z-30 transition-all duration-300 flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-60'
      ]"
    >
      <div class="flex items-center h-16 px-4 border-b border-gray-700/50">
        <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
          <Database class="w-5 h-5 text-white" />
        </div>
        <span v-if="!sidebarCollapsed" class="ml-3 text-white font-semibold text-base whitespace-nowrap">SmartBackup</span>
      </div>

      <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-link"
          :class="{ active: isActive(item.path) }"
        >
          <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
          <span v-if="!sidebarCollapsed" class="text-sm whitespace-nowrap">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-700/50">
        <button
          @click="toggleSidebar"
          class="w-full flex items-center justify-center p-2 text-gray-400 hover:text-white rounded-lg hover:bg-sidebar-hover transition-colors"
        >
          <ChevronLeft v-if="!sidebarCollapsed" class="w-5 h-5" />
          <ChevronRight v-else class="w-5 h-5" />
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div :class="['flex-1 flex flex-col transition-all duration-300', sidebarCollapsed ? 'ml-16' : 'ml-60']">
      <!-- Top Bar -->
      <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-20">
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-semibold text-gray-800">{{ currentTitle }}</h2>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse-dot" />
            <span v-if="systemStatus">{{ systemStatus.online_clients }} 在线</span>
          </div>

          <el-dropdown trigger="click">
            <button class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <div class="w-7 h-7 bg-primary rounded-full flex items-center justify-center">
                <User class="w-4 h-4 text-white" />
              </div>
              <span class="text-sm text-gray-700">{{ auth.user?.username || '用户' }}</span>
              <ChevronDown class="w-4 h-4 text-gray-400" />
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/system')">
                  <Settings class="w-4 h-4 inline mr-2" />系统设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="auth.logout()">
                  <LogOut class="w-4 h-4 inline mr-2" />退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto p-6 bg-[#F2F3F5]">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import {
  LayoutDashboard, Monitor, FolderTree, FileText, HardDrive,
  PackageOpen, Settings, Database, User, ChevronDown, LogOut,
  ChevronLeft, ChevronRight
} from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const app = useAppStore()

const { sidebarCollapsed, systemStatus } = app
const toggleSidebar = app.toggleSidebar

const menuItems = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { path: '/clients', label: '客户端管理', icon: Monitor },
  { path: '/groups', label: '分组管理', icon: FolderTree },
  { path: '/policies', label: '策略模板', icon: FileText },
  { path: '/storages', label: '存储后端', icon: HardDrive },
  { path: '/versions', label: '版本管理', icon: PackageOpen },
  { path: '/system', label: '系统设置', icon: Settings, adminOnly: true },
]

const currentTitle = computed(() => {
  const item = menuItems.find(m => route.path.startsWith(m.path))
  return item?.label || ''
})

function isActive(path: string): boolean {
  return route.path === path || (path !== '/dashboard' && route.path.startsWith(path))
}

onMounted(() => {
  app.fetchSystemStatus()
})
</script>
