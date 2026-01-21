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
/* =====================================================
   Bento Grids / Apple Style - Asset Card
   ===================================================== */

.asset-card {
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  
  /* Bento 风格纯白卡片 */
  background: #FFFFFF;
  border: none;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.04),
    0 8px 16px rgba(0, 0, 0, 0.06);
  
  /* 24px 大圆角 */
  border-radius: 20px;
  
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 悬停效果 */
.asset-card:hover {
  transform: translateY(-6px);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 16px 32px rgba(0, 0, 0, 0.12);
}

/* 选中状态 */
.asset-card.selected {
  border: 2px solid #007AFF;
  box-shadow: 
    0 0 0 4px rgba(0, 122, 255, 0.15),
    0 8px 16px rgba(0, 0, 0, 0.08);
}

.card-image {
  position: relative;
  width: 100%;
  height: 160px;
  flex-shrink: 0;
  overflow: hidden;
  background: #F5F5F7;
  border-radius: 20px 20px 0 0;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
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
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: all 0.25s ease;
  z-index: 5;
}

.asset-card:hover .image-overlay {
  opacity: 1;
}

/* 悬停按钮 - Apple 风格 */
.image-overlay :deep(.el-button) {
  background: #FFFFFF !important;
  border: none !important;
  color: #1D1D1F !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.image-overlay :deep(.el-button:hover) {
  background: #007AFF !important;
  color: #FFFFFF !important;
}

/* Checkbox 样式 */
:deep(.el-checkbox__inner) {
  background-color: #FFFFFF;
  border-color: #D2D2D7;
  border-radius: 6px;
  width: 20px;
  height: 20px;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #007AFF;
  border-color: #007AFF;
}

:deep(.el-checkbox__inner::after) {
  left: 8px;
  top: 5px;
  width: 4px;
  height: 8px;
  border-width: 1px;
}

.card-checkbox {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
}

/* 卡片内容区 */
.card-content {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #1D1D1F;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  margin-bottom: auto;
}

/* Tag 样式 */
.card-meta :deep(.el-tag) {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
}

.card-info {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-top: 1px solid #E8E8ED;
  padding-top: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #86868B;
}

.info-item .el-icon {
  color: #AEAEB2;
}
</style>
