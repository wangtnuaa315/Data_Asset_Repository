<template>
  <div class="app-container">
    <!-- 顶部标题栏（登录页和管理页不显示） -->
    <header class="app-header" v-if="showHeader">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="28"><DataAnalysis /></el-icon>
          <span class="logo-text">数据资产检索系统</span>
        </div>
        <div class="header-actions">
          <el-button
            v-if="isLoggedIn"
            :icon="Setting"
            @click="goToAdmin"
          >
            管理中心
          </el-button>
          <el-dropdown v-if="isLoggedIn" @command="handleUserCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ username }}
              <el-tag v-if="isAdmin" size="small" type="success">管理员</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-else type="primary" @click="goToLogin">登录</el-button>
        </div>
      </div>
    </header>

    <!-- 业务模块Tab栏 -->
    <nav class="business-tabs" v-if="showTabs">
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Warning, Document, Setting, User } from '@element-plus/icons-vue'
import authApi from './api/auth'

const router = useRouter()
const route = useRoute()
const activeTab = ref('emergency')

// 用户状态
const isLoggedIn = computed(() => authApi.isLoggedIn())
const isAdmin = computed(() => authApi.isAdmin())
const username = computed(() => localStorage.getItem('username') || '')

// 是否显示Header（登录页不显示）
const showHeader = computed(() => {
  return route.name !== 'Login'
})

// 是否显示Tab栏（登录页和管理页不显示）
const showTabs = computed(() => {
  return !['Login', 'Admin'].includes(route.name)
})

const handleTabClick = (tab) => {
  if (tab.paneName !== 'court') {
    router.push(`/${tab.paneName}`)
  }
}

const goToAdmin = () => {
  if (!isAdmin.value) {
    ElMessage.warning('需要管理员权限，请使用admin账号登录')
    router.push('/login')
    return
  }
  router.push('/admin')
}

const goToLogin = () => {
  router.push('/login')
}

const handleUserCommand = (command) => {
  if (command === 'logout') {
    authApi.logout()
    ElMessage.success('已退出登录')
    // 强制刷新页面
    window.location.href = '/login'
  }
}

// 监听路由变化更新Tab
watch(() => route.name, (name) => {
  if (name === 'Emergency') {
    activeTab.value = 'emergency'
  }
})

onMounted(() => {
  if (route.name === 'Emergency') {
    activeTab.value = 'emergency'
  }
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent; /* 使用body的全局背景 */
}

.app-header {
  /* 磨砂玻璃效果 Header */
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.header-content {
  max-width: 1800px;
  margin: 0 auto;
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.15);
  transition: all 0.2s ease;
}

.user-info:hover {
  background: rgba(59, 130, 246, 0.15);
  color: var(--primary-color);
  border-color: rgba(59, 130, 246, 0.3);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--primary-color);
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-heading);
}

.logo-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
}

/* 业务Tab栏样式 - 悬浮胶囊风格 */
.business-tabs {
  background: transparent;
  padding: 16px 32px 0;
  display: flex;
  justify-content: center; /* 居中显示 */
}

:deep(.el-tabs__header) {
  margin: 0;
  border-bottom: none;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

/* Tab项样式 */
:deep(.el-tabs__item) {
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 600;
  padding: 0 32px !important;
  height: 48px;
  line-height: 48px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

:deep(.el-tabs__item:hover) {
  color: var(--primary-color);
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  font-weight: bold;
}

/* 自定义底部激活条为发光背景 */
/* 自定义底部激活条 */
:deep(.el-tabs__active-bar) {
  height: 3px;
  background-color: var(--primary-color);
  border-radius: 3px;
  bottom: 0px;
}

:deep(.el-tabs__item.is-disabled) {
  color: var(--text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-label .el-tag {
  margin-left: 6px;
  font-size: 10px;
  border: none;
}

.app-main {
  flex: 1;
  overflow: hidden;
  padding: 24px 32px;
  background: transparent;
  position: relative;
}
</style>
