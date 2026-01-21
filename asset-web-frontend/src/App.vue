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
          <!-- 操作指南入口 - 仅管理员可见 -->
          <el-tooltip v-if="isAdmin" content="操作指南" placement="bottom">
            <div class="help-btn" :class="{ 'pulse': showGuidePulse }" @click="goToAdmin">
              <el-icon :size="20"><QuestionFilled /></el-icon>
            </div>
          </el-tooltip>
          
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
        <el-tab-pane name="court">
          <template #label>
            <span class="tab-label">
              <el-icon><Document /></el-icon>
              <span>法院案件</span>
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="legal">
          <template #label>
            <span class="tab-label">
              <el-icon><Reading /></el-icon>
              <span>法律文书</span>
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
import { DataAnalysis, Warning, Document, User, QuestionFilled, Reading } from '@element-plus/icons-vue'
import authApi from './api/auth'

const router = useRouter()
const route = useRoute()
const activeTab = ref('emergency')

// 用户状态
const isLoggedIn = computed(() => authApi.isLoggedIn())
const isAdmin = computed(() => authApi.isAdmin())
const username = computed(() => localStorage.getItem('username') || '')

// 操作指南动态引导 - 登录后短暂显示脉冲动画
const showGuidePulse = ref(false)

onMounted(() => {
  // 登录后显示脉冲动画 5 秒
  if (authApi.isLoggedIn()) {
    showGuidePulse.value = true
    setTimeout(() => {
      showGuidePulse.value = false
    }, 5000)
  }
})

// 是否显示Header（登录页不显示）
const showHeader = computed(() => {
  return route.name !== 'Login'
})

// 是否显示Tab栏（登录页和管理页不显示）
const showTabs = computed(() => {
  return !['Login', 'Admin'].includes(route.name)
})

const handleTabClick = (tab) => {
  router.push(`/${tab.paneName}`)
}

const goToAdmin = () => {
  showGuidePulse.value = false  // 停止动画
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
/* =====================================================
   Bento Grids / Apple Style - App Layout
   ===================================================== */

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
  position: relative;
  z-index: 1;
}

/* Bento 风格 Header - 纯白清爽 */
.app-header {
  background: #FFFFFF;
  border-bottom: 1px solid var(--border-light, #E8E8ED);
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 12px rgba(0, 0, 0, 0.03);
  z-index: 100;
  position: relative;
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

/* 帮助按钮 - 动态引导 */
.help-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  cursor: pointer;
  transition: all 0.2s ease;
}

.help-btn:hover {
  background: #007AFF;
  color: white;
  transform: scale(1.05);
}

/* 脉冲动画 - 吸引注意 */
.help-btn.pulse {
  animation: pulse-ring 1.5s ease-out infinite;
}

@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 122, 255, 0.5);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(0, 122, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 122, 255, 0);
  }
}

/* Apple 风格用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary, #86868B);
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(0, 122, 255, 0.08);
  border: 1px solid rgba(0, 122, 255, 0.15);
  transition: all 0.2s ease;
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 14px;
}

.user-info:hover {
  background: rgba(0, 122, 255, 0.15);
  color: var(--primary-color, #007AFF);
  border-color: rgba(0, 122, 255, 0.3);
}

/* Apple 风格 Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--primary-color, #007AFF);
  font-size: 20px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
}

.logo-text {
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

/* Bento 风格 Tab 栏 */
.business-tabs {
  background: #FFFFFF;
  padding: 8px 32px 0;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid var(--border-light, #E8E8ED);
}

:deep(.el-tabs__header) {
  margin: 0;
  border-bottom: none;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

/* Apple 风格 Tab 项 */
:deep(.el-tabs__item) {
  color: var(--text-secondary, #86868B);
  font-size: 15px;
  font-weight: 500;
  font-family: 'Inter', -apple-system, sans-serif;
  padding: 0 28px !important;
  height: 44px;
  line-height: 44px;
  transition: all 0.2s ease;
}

:deep(.el-tabs__item:hover) {
  color: var(--primary-color, #007AFF);
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color, #007AFF);
  font-weight: 600;
}

/* Apple 底部激活条 */
:deep(.el-tabs__active-bar) {
  height: 3px;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  border-radius: 3px 3px 0 0;
  bottom: 0;
}

:deep(.el-tabs__item.is-disabled) {
  color: var(--text-muted, #AEAEB2);
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
  border-radius: 10px;
}

/* 主内容区 */
.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px 32px;
  background: transparent;
  position: relative;
  z-index: 1;
}
</style>
