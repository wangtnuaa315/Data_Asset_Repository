<template>
  <div class="admin-layout">
    <!-- 顶部栏 -->
    <header class="admin-header">
      <div class="header-left">
        <el-icon :size="24"><Setting /></el-icon>
        <h1>管理中心</h1>
      </div>
      <el-button @click="goBack" :icon="Back">返回检索</el-button>
    </header>

    <div class="admin-body">
      <!-- 侧边导航 -->
      <aside class="admin-sidebar">
        <nav class="sidebar-nav">
          <router-link 
            v-for="item in navItems" 
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ 'is-disabled': item.disabled }"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
            <el-tag v-if="item.tag" size="small" type="info">{{ item.tag }}</el-tag>
          </router-link>
        </nav>
      </aside>

      <!-- 主内容区 -->
      <main class="admin-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Setting, Back, DataAnalysis, Warning, Document, Tools } from '@element-plus/icons-vue'

const router = useRouter()

const navItems = [
  { path: '/admin', label: '总览', icon: DataAnalysis },
  { path: '/admin/emergency', label: '应急安全', icon: Warning },
  { path: '/admin/court', label: '法院案件', icon: Document, disabled: true, tag: '即将上线' },
  { path: '/admin/system', label: '系统设置', icon: Tools }
]

const goBack = () => {
  router.push('/emergency')
}
</script>

<style scoped>
/* Bento Grids / Apple Style - Admin Layout */

.admin-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  position: relative;
  z-index: 1;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8E8ED;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  font-size: 20px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.header-left .el-icon {
  color: #007AFF;
}

.admin-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.admin-sidebar {
  width: 240px;
  background: #FFFFFF;
  border-right: 1px solid #E8E8ED;
  padding: 24px 16px;
  flex-shrink: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  color: #86868B;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Inter', -apple-system, sans-serif;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(0, 122, 255, 0.08);
  color: #007AFF;
}

.nav-item.router-link-exact-active {
  background: rgba(0, 122, 255, 0.12);
  color: #007AFF;
  font-weight: 600;
}

.nav-item.is-disabled {
  opacity: 0.5;
  pointer-events: none;
}

.nav-item .el-tag {
  margin-left: auto;
  font-size: 10px;
}

.admin-main {
  flex: 1;
  padding: 24px 32px;
  overflow: auto;
  background: transparent;
}
</style>
