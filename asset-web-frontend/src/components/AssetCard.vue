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
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  background: rgba(26, 31, 58, 0.3);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.asset-card:hover {
  transform: translateY(-5px) scale(1.02);
  border-color: var(--primary-color);
  box-shadow: 0 10px 30px -10px rgba(0, 212, 255, 0.3);
  z-index: 10;
}

.asset-card.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
  background: rgba(0, 212, 255, 0.1);
}

.card-image {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px 8px 0 0;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.asset-card:hover .card-image img {
  transform: scale(1.15);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(13, 17, 34, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
  backdrop-filter: blur(2px);
}

.asset-card:hover .image-overlay {
  opacity: 1;
}

.card-checkbox {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
  transform: scale(1.1);
}

:deep(.el-checkbox__inner) {
  background-color: rgba(26, 31, 58, 0.9);
  border-color: rgba(255, 255, 255, 0.3);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  box-shadow: 0 0 10px var(--primary-color);
}

.card-content {
  padding: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.card-meta {
  margin-bottom: 12px;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.info-item .el-icon {
  color: var(--primary-color);
  filter: drop-shadow(0 0 2px var(--primary-color));
}
</style>
