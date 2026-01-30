<template>
  <div class="app-container">
    <!-- 动态光效背景 -->
    <div class="background-effects" v-if="showHeader">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 顶部标题栏（登录页和管理页不显示） -->
    <header class="app-header glass-header" v-if="showHeader">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon-wrapper">
            <el-icon :size="24"><DataAnalysis /></el-icon>
          </div>
          <span class="logo-text">数据资产检索系统</span>
        </div>
        <div class="header-actions">
          <!-- 操作指南入口 - 仅管理员可见 -->
          <el-tooltip v-if="isAdmin" content="操作指南" placement="bottom">
            <div class="help-btn glass-btn" :class="{ 'pulse': showGuidePulse }" @click="goToAdmin">
              <el-icon :size="18"><QuestionFilled /></el-icon>
            </div>
          </el-tooltip>
          
          <el-dropdown v-if="isLoggedIn" @command="handleUserCommand">
            <span class="user-info glass-btn">
              <el-icon><User /></el-icon>
              {{ username }}
              <el-tag v-if="isAdmin" size="small" type="success" effect="plain">管理员</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-else type="primary" @click="goToLogin" class="login-btn-header">登录</el-button>
        </div>
      </div>
    </header>

    <!-- 业务模块Tab栏 -->
    <nav class="business-tabs glass-tabs" v-if="showTabs">
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
  } else if (name === 'Court') {
    activeTab.value = 'court'
  } else if (name === 'Legal') {
    activeTab.value = 'legal'
  }
})

onMounted(() => {
  if (route.name === 'Emergency') {
    activeTab.value = 'emergency'
  } else if (route.name === 'Court') {
    activeTab.value = 'court'
  } else if (route.name === 'Legal') {
    activeTab.value = 'legal'
  }
})
</script>

<style scoped>
/* =====================================================
   Glassmorphism App Layout
   紫蓝渐变背景 + 毛玻璃导航
   ===================================================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  
  /* 主渐变背景 */
  background: linear-gradient(135deg, 
    #1a1a2e 0%, 
    #16213e 25%, 
    #0f3460 50%, 
    #533483 75%, 
    #e94560 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 动态光效球 */
.background-effects {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.5;
}

.orb-1 {
  width: 700px;
  height: 700px;
  background: radial-gradient(circle, #667eea 0%, transparent 70%);
  top: -200px;
  left: -150px;
  animation: float 12s ease-in-out infinite;
}

.orb-2 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #764ba2 0%, transparent 70%);
  bottom: -200px;
  right: -150px;
  animation: float 15s ease-in-out infinite reverse;
}

.orb-3 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 40%;
  left: 60%;
  animation: pulse 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-40px) rotate(5deg); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.15); opacity: 0.5; }
}

/* 玻璃态 Header */
.app-header.glass-header {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
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

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon-wrapper {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

/* 玻璃按钮通用样式 */
.glass-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.glass-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

/* 帮助按钮 */
.help-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
}

.help-btn:hover {
  color: white;
}

/* 脉冲动画 */
.help-btn.pulse {
  animation: pulse-ring 1.5s ease-out infinite;
}

@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.6); }
  70% { box-shadow: 0 0 0 12px rgba(102, 126, 234, 0); }
  100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.9);
  padding: 8px 16px;
  font-size: 14px;
}

.user-info .el-tag {
  background: rgba(52, 199, 89, 0.2);
  border: 1px solid rgba(52, 199, 89, 0.3);
  color: #34C759;
}

/* Header 登录按钮 */
.login-btn-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 10px 24px !important;
  font-weight: 600 !important;
}

/* 玻璃态 Tab 栏 */
.business-tabs.glass-tabs {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px 32px 0;
  display: flex;
  justify-content: center;
  position: relative;
  z-index: 50;
}

:deep(.el-tabs__header) {
  margin: 0;
  border-bottom: none;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

/* Tab 项样式 */
:deep(.el-tabs__item) {
  color: rgba(255, 255, 255, 0.6);
  font-size: 15px;
  font-weight: 500;
  font-family: 'Inter', -apple-system, sans-serif;
  padding: 0 28px !important;
  height: 48px;
  line-height: 48px;
  transition: all 0.3s ease;
}

:deep(.el-tabs__item:hover) {
  color: rgba(255, 255, 255, 0.9);
}

:deep(.el-tabs__item.is-active) {
  color: #FFFFFF;
  font-weight: 600;
}

/* 渐变激活条 */
:deep(.el-tabs__active-bar) {
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px 3px 0 0;
  bottom: 0;
  box-shadow: 0 0 12px rgba(102, 126, 234, 0.5);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主内容区 */
.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px 32px;
  position: relative;
  z-index: 1;
}

/* 滚动条美化 */
.app-main::-webkit-scrollbar {
  width: 8px;
}

.app-main::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.app-main::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.app-main::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
</style>
