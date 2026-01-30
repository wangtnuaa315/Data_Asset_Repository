<template>
  <el-dialog
    v-model="visible"
    title="资产详情"
    width="800px"
    :before-close="handleClose"
    :append-to-body="true"
    class="glass-detail-dialog"
  >
    <div v-if="asset" class="detail-scroll-content">
      <div class="detail-container">
        <!-- 大图预览 -->
        <div class="image-preview">
          <img 
            :src="asset.thumbnail_url.replace('/thumbnail/', '/download/')" 
            :alt="asset.filename"
            @error="handleImageError"
          />
        </div>

        <!-- 详细信息 -->
        <el-descriptions :column="2" border class="detail-info" :label-class-name="'detail-label'">
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

          <el-descriptions-item label="文件路径" :span="2">
            <span class="filepath-text">{{ asset.filepath }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" :icon="CopyDocument" @click="copyPath">
          复制路径
        </el-button>
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
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ElMessage.success('路径已复制到剪贴板')
    } else {
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
/* 滚动容器 - 与法律文书一致的高度限制 */
.detail-scroll-content {
  max-height: 50vh;
  overflow-y: auto;
  padding-right: 8px;
}

.detail-scroll-content::-webkit-scrollbar {
  width: 6px;
}

.detail-scroll-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.detail-scroll-content::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

.detail-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-preview {
  width: 100%;
  max-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  overflow: hidden;
}

.image-preview img {
  max-width: 100%;
  max-height: 220px;
  object-fit: contain;
}

.filepath-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  word-break: break-all;
}

.detail-info {
  margin-top: 12px;
}

/* 标签列宽度调整 */
:deep(.el-descriptions__label) {
  width: 90px !important;
  min-width: 90px !important;
  white-space: nowrap !important;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
