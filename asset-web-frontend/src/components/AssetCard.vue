<template>
  <el-card 
    class="asset-card" 
    :class="{ 'selected': selected }"
    @click="$emit('view-detail')"
  >
    <div class="card-image">
      <img 
        :src="asset.thumbnail_url" 
        :alt="asset.filename"
        @error="handleImageError"
      />
      <div class="image-overlay">
        <el-button circle :icon="ZoomIn" @click.stop="$emit('view-detail')" />
        <el-button circle :icon="Download" @click.stop="handleDownload" />
      </div>
      <el-checkbox 
        :model-value="selected"
        class="card-checkbox"
        @click.stop
        @change="$emit('select')"
      />
    </div>

    <div class="card-content">
      <div class="card-title" :title="asset.filename">
        {{ asset.filename }}
      </div>
      
      <div class="card-meta">
        <el-tag type="info" effect="dark" size="small">
          {{ asset.alarm_name }}
        </el-tag>
      </div>

      <div class="card-info">
        <div class="info-item">
          <el-icon><Clock /></el-icon>
          <span>{{ formatDate(asset.alarm_time) }}</span>
        </div>
        <div class="info-item" v-if="asset.dev_code">
          <el-icon><Connection /></el-icon>
          <span>{{ asset.dev_code }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ZoomIn, Download, Clock, Connection } from '@element-plus/icons-vue'
import api from '../api/emergency'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'view-detail'])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleImageError = (e) => {
  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23374151" width="200" height="200"/%3E%3Ctext fill="%239ca3af" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3E加载失败%3C/text%3E%3C/svg%3E'
}

const handleDownload = () => {
  const url = api.getDownloadUrl(props.asset.asset_id)
  const a = document.createElement('a')
  a.href = url
  a.download = props.asset.filename
  a.click()
}
</script>

<style scoped>
.asset-card {
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  
  /* 强制 Glassmorphism - 用户规范 */
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.07);
  
  /* 16px 圆角 */
  border-radius: 16px;
  
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 交互微效 - translateY(-4px) + 阴影加深 */
.asset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(31, 38, 135, 0.15);
}

.card-image {
  position: relative;
  width: 100%;
  height: 160px; /* Reduced height */
  flex-shrink: 0;
  overflow: hidden;
  background: #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.asset-card:hover .card-image img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3); /* Lighter overlay */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: all 0.2s ease;
  backdrop-filter: blur(2px);
  z-index: 5;
}

.asset-card:hover .image-overlay {
  opacity: 1;
}

/* Light theme checkbox styles */
:deep(.el-checkbox__inner) {
  background-color: #fff;
  border-color: #cbd5e1;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.card-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
}

.card-content {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-shadow: none;
}

.card-meta {
  margin-bottom: auto; /* Push info to bottom */
}

.card-info {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: inherit; /* Remove monospaced font constraint */
}

.info-item .el-icon {
  color: var(--text-muted);
  filter: none;
}
</style>
