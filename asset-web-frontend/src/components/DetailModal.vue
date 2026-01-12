<template>
  <el-dialog
    v-model="visible"
    title="资产详情"
    width="800px"
    :before-close="handleClose"
  >
    <div v-if="asset" class="detail-container">
      <!-- 大图预览 -->
      <div class="image-preview">
        <img 
          :src="asset.thumbnail_url.replace('/thumbnail/', '/download/')" 
          :alt="asset.filename"
          @error="handleImageError"
        />
      </div>

      <!-- 详细信息 -->
      <el-descriptions :column="2" border class="detail-info">
        <el-descriptions-item label="文件名">
          {{ asset.filename }}
        </el-descriptions-item>
        
        <el-descriptions-item label="文件大小">
          {{ formatFileSize(asset.filesize) }}
        </el-descriptions-item>

        <el-descriptions-item label="告警名称">
          <el-tag type="warning" effect="dark">
            {{ asset.alarm_name }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="告警时间">
          {{ formatDate(asset.alarm_time) }}
        </el-descriptions-item>

        <el-descriptions-item label="设备编码" v-if="asset.dev_code">
          <el-tag type="info">{{ asset.dev_code }}</el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="资产ID">
          #{{ asset.asset_id }}
        </el-descriptions-item>

        <el-descriptions-item label="AI分析" :span="2">
          <el-tag 
            v-if="asset.analysis && asset.analysis.trim()" 
            type="success" 
            effect="dark"
            size="default"
          >
            {{ asset.analysis }}
          </el-tag>
          <span v-else class="no-analysis">暂无分析数据</span>
        </el-descriptions-item>

        <el-descriptions-item label="文件路径" :span="2">
          <el-input 
            :model-value="asset.filepath" 
            readonly 
            size="small"
          >
            <template #append>
              <el-button 
                :icon="CopyDocument" 
                @click="copyPath"
              >复制</el-button>
            </template>
          </el-input>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" :icon="Download" @click="handleDownload">
          下载文件
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, CopyDocument } from '@element-plus/icons-vue'
import api from '../api/emergency'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  asset: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

const handleImageError = (e) => {
  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="400"%3E%3Crect fill="%23374151" width="600" height="400"/%3E%3Ctext fill="%239ca3af" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3E加载失败%3C/text%3E%3C/svg%3E'
}

const copyPath = async () => {
  const text = props.asset.filepath
  try {
    // 尝试使用现代Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ElMessage.success('路径已复制到剪贴板')
    } else {
      // 兼容方案：使用传统的execCommand
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-9999px'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success('路径已复制到剪贴板')
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

const handleDownload = () => {
  const url = api.getDownloadUrl(props.asset.asset_id)
  const a = document.createElement('a')
  a.href = url
  a.download = props.asset.filename
  a.click()
  ElMessage.success('开始下载')
}
</script>

<style scoped>
.detail-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-preview {
  width: 100%;
  max-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 8px;
  overflow: hidden;
}

.image-preview img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.detail-info {
  margin-top: 20px;
}

.no-analysis {
  color: #9ca3af;
  font-size: 14px;
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog) {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 47, 247, 0.1) 100%);
}

:deep(.el-dialog__title) {
  color: var(--primary-color);
  font-weight: 600;
}
</style>
