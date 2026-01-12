<template>
  <div class="app-container">
    <!-- 顶部标题栏 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="28"><DataAnalysis /></el-icon>
          <span class="logo-text">数据资产检索系统</span>
        </div>
      </div>
    </header>

    <!-- 业务模块Tab栏 -->
    <nav class="business-tabs">
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane name="emergency">
          <template #label>
            <span class="tab-label">
              <el-icon><Warning /></el-icon>
              <span>应急安全</span>
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="court" disabled>
          <template #label>
            <span class="tab-label">
              <el-icon><Document /></el-icon>
              <span>法院案件</span>
              <el-tag size="small" type="info">即将上线</el-tag>
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </nav>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Warning, Document } from '@element-plus/icons-vue'

const router = useRouter()
const activeTab = ref('emergency')

const handleTabClick = (tab) => {
  if (tab.paneName !== 'court') {
    router.push(`/${tab.paneName}`)
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

.app-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 32px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--primary-color);
  font-size: 20px;
  font-weight: 700;
}

.logo-text {
  background: linear-gradient(135deg, #fff 0%, var(--primary-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
}

/* 业务Tab栏样式 */
.business-tabs {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 0 32px;
}

:deep(.el-tabs__header) {
  margin: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  padding: 0 20px;
  height: 44px;
  line-height: 44px;
}

:deep(.el-tabs__item:hover) {
  color: var(--text-primary);
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
}

:deep(.el-tabs__active-bar) {
  background-color: var(--primary-color);
  height: 3px;
}

:deep(.el-tabs__item.is-disabled) {
  color: var(--text-muted);
  cursor: not-allowed;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-label .el-tag {
  margin-left: 6px;
  font-size: 11px;
}

.app-main {
  flex: 1;
  overflow: hidden;
  padding: 20px 32px;
  background: var(--bg-primary);
}
</style>
