<template>
  <el-dialog :model-value="visible" :title="title" width="420px" @update:model-value="$emit('update:visible', $event)" :close-on-click-modal="false">
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center flex-shrink-0">
        <AlertCircle class="w-5 h-5 text-danger" />
      </div>
      <div>
        <p class="text-sm text-gray-700">{{ message }}</p>
        <p v-if="detail" class="text-xs text-gray-400 mt-1">{{ detail }}</p>
      </div>
    </div>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="danger" @click="$emit('confirm')" :loading="loading">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { AlertCircle } from 'lucide-vue-next'

defineProps<{
  visible: boolean
  title?: string
  message: string
  detail?: string
  loading?: boolean
}>()

defineEmits<{
  'update:visible': [value: boolean]
  'confirm': []
}>()
</script>
