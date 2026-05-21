<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card flex items-center gap-4">
        <div class="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
          <Monitor class="w-6 h-6 text-primary" />
        </div>
        <div>
          <p class="text-sm text-gray-500">在线客户端</p>
          <p class="text-2xl font-bold text-gray-800">{{ status?.online_clients || 0 }}</p>
          <p class="text-xs text-gray-400">共 {{ status?.total_clients || 0 }} 台</p>
        </div>
      </div>

      <div class="card flex items-center gap-4">
        <div class="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
          <HardDrive class="w-6 h-6 text-success" />
        </div>
        <div>
          <p class="text-sm text-gray-500">今日备份任务</p>
          <p class="text-2xl font-bold text-gray-800">{{ status?.total_backups_today || 0 }}</p>
          <p class="text-xs text-green-500">
            <TrendingUp class="w-3 h-3 inline" /> 运行中
          </p>
        </div>
      </div>

      <div class="card flex items-center gap-4">
        <div class="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center">
          <Database class="w-6 h-6 text-purple-500" />
        </div>
        <div>
          <p class="text-sm text-gray-500">存储后端</p>
          <p class="text-2xl font-bold text-gray-800">{{ status?.total_storages || 0 }}</p>
          <p class="text-xs text-gray-400">活跃配置</p>
        </div>
      </div>

      <div class="card flex items-center gap-4">
        <div class="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center">
          <AlertCircle class="w-6 h-6 text-warning" />
        </div>
        <div>
          <p class="text-sm text-gray-500">系统告警</p>
          <p class="text-2xl font-bold text-gray-800">0</p>
          <p class="text-xs text-success">无异常</p>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div class="card lg:col-span-2">
        <h3 class="text-base font-semibold text-gray-800 mb-4">最近7天备份趋势</h3>
        <v-chart :option="backupTrendOption" style="height: 300px" autoresize />
      </div>
      <div class="card">
        <h3 class="text-base font-semibold text-gray-800 mb-4">存储类型分布</h3>
        <v-chart :option="storageDistOption" style="height: 300px" autoresize />
      </div>
    </div>

    <!-- Recent Backups Table -->
    <div class="card">
      <h3 class="text-base font-semibold text-gray-800 mb-4">最近备份记录</h3>
      <el-table :data="recentBackups" style="width: 100%" size="default" stripe>
        <el-table-column prop="source_device" label="来源" min-width="150" />
        <el-table-column prop="file_count" label="文件数" width="100" align="center" />
        <el-table-column prop="total_size" label="大小" width="120" align="center">
          <template #default="{ row }">
            {{ formatSize(row.total_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <span
              :class="[
                'badge',
                row.status === 'completed' ? 'badge-success' :
                row.status === 'failed' ? 'badge-danger' : 'badge-info'
              ]"
            >
              {{ row.status === 'completed' ? '已完成' : row.status === 'failed' ? '失败' : '进行中' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" min-width="160">
          <template #default="{ row }">
            {{ row.completed_at || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Monitor, HardDrive, Database, TrendingUp, AlertCircle } from 'lucide-vue-next'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getSystemStatus } from '@/api/system'
import { getBackups } from '@/api/backups'
import type { SystemStatus, BackupRecord } from '@/types'

use([CanvasRenderer, LineChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const status = ref<SystemStatus | null>(null)
const recentBackups = ref<BackupRecord[]>([])

const backupTrendOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['5/13', '5/14', '5/15', '5/16', '5/17', '5/18', '5/19'] },
  yAxis: { type: 'value' },
  series: [
    {
      name: '备份任务数',
      type: 'line',
      smooth: true,
      data: [12, 15, 8, 22, 18, 14, 20],
      areaStyle: { color: 'rgba(64, 158, 255, 0.15)' },
      lineStyle: { color: '#409EFF' },
      itemStyle: { color: '#409EFF' },
    },
  ],
}

const storageDistOption = {
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%' },
  series: [
    {
      name: '存储类型',
      type: 'pie',
      radius: ['50%', '75%'],
      avoidLabelOverlap: false,
      label: { show: false },
      data: [
        { value: 3, name: '本地存储' },
        { value: 2, name: 'S3' },
        { value: 1, name: 'SFTP' },
      ],
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
      },
    },
  ],
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

onMounted(async () => {
  try {
    status.value = await getSystemStatus()
  } catch {
    console.error('Failed to load system status')
  }
  try {
    const res = await getBackups({ page: 1, page_size: 10 })
    recentBackups.value = res.items
  } catch {
    console.error('Failed to load backups')
  }
})
</script>
