<template>
  <div class="admin-hub">
    <div class="hub-header">
      <h2>业务模块</h2>
      <p>选择要管理的业务模块</p>
    </div>

    <div class="module-grid">
      <!-- 应急安全模块 -->
      <div class="module-card" @click="$router.push('/admin/emergency')">
        <div class="card-icon emergency">
          <el-icon :size="32"><Warning /></el-icon>
        </div>
        <div class="card-content">
          <h3>应急安全</h3>
          <p>管理告警资产、数据导入、AI分析配置</p>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>

      <!-- 法院案件模块 -->
      <div class="module-card disabled">
        <div class="card-icon court">
          <el-icon :size="32"><Document /></el-icon>
        </div>
        <div class="card-content">
          <h3>法院案件</h3>
          <p>管理案件数据、法律文书、归档记录</p>
          <el-tag size="small" type="info">即将上线</el-tag>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>

      <!-- 系统设置模块 -->
      <div class="module-card" @click="$router.push('/admin/system')">
        <div class="card-icon system">
          <el-icon :size="32"><Tools /></el-icon>
        </div>
        <div class="card-content">
          <h3>系统设置</h3>
          <p>文件管理、脚本执行、系统配置</p>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2>快捷操作</h2>
      <div class="action-grid">
        <el-button type="primary" :icon="Upload" @click="$router.push('/admin/system')">
          上传文件
        </el-button>
        <el-button :icon="Refresh" @click="$router.push('/admin/emergency')">
          数据导入
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Warning, Document, Tools, ArrowRight, Upload, Refresh } from '@element-plus/icons-vue'
</script>

<style scoped>
/* Bento Grids / Apple Style - Admin Hub */

.admin-hub {
  max-width: 1000px;
  margin: 0 auto;
}

.hub-header {
  margin-bottom: 32px;
}

.hub-header h2 {
  font-size: 24px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #1D1D1F;
  margin: 0 0 8px 0;
}

.hub-header p {
  color: #86868B;
  font-size: 15px;
  margin: 0;
}

/* 模块卡片网格 */
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.module-card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.04),
    0 8px 16px rgba(0, 0, 0, 0.06);
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 16px 32px rgba(0, 0, 0, 0.12);
}

.module-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.module-card.disabled:hover {
  transform: none;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.04),
    0 8px 16px rgba(0, 0, 0, 0.06);
}

.card-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon.emergency {
  background: linear-gradient(135deg, #FF3B30 0%, #FF9500 100%);
  color: white;
}

.card-icon.court {
  background: linear-gradient(135deg, #5856D6 0%, #AF52DE 100%);
  color: white;
}

.card-icon.system {
  background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%);
  color: white;
}

.card-content {
  flex: 1;
}

.card-content h3 {
  font-size: 17px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #1D1D1F;
  margin: 0 0 6px 0;
}

.card-content p {
  font-size: 13px;
  color: #86868B;
  margin: 0;
}

.card-content .el-tag {
  margin-top: 8px;
}

.arrow {
  color: #AEAEB2;
  font-size: 20px;
}

/* 快捷操作 */
.quick-actions h2 {
  font-size: 18px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #1D1D1F;
  margin: 0 0 16px 0;
}

.action-grid {
  display: flex;
  gap: 12px;
}

.action-grid :deep(.el-button) {
  border-radius: 12px;
  height: 44px;
  font-weight: 500;
}
</style>
