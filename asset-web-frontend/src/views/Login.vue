<template>
  <div class="login-container">
    <!-- 动态光效背景 -->
    <div class="background-effects">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 玻璃态登录卡片 -->
    <div class="login-card glass-card">
      <div class="login-header">
        <div class="logo-container">
          <el-icon :size="32" class="logo-icon"><DataAnalysis /></el-icon>
        </div>
        <h1>数据资产检索系统</h1>
        <p>欢迎回来，请登录继续</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <div class="input-wrapper">
            <el-icon class="input-icon"><User /></el-icon>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              class="glass-input"
            />
          </div>
        </el-form-item>

        <el-form-item prop="password">
          <div class="input-wrapper">
            <el-icon class="input-icon"><Lock /></el-icon>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              class="glass-input"
              @keyup.enter="handleLogin"
            />
          </div>
        </el-form-item>

        <el-form-item>
          <div class="input-wrapper">
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              <span v-if="!loading">登  录</span>
              <span v-else>登录中...</span>
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <div class="hint-box">
          <el-icon><InfoFilled /></el-icon>
          <span>体验账号：user / user123</span>
        </div>
      </div>
    </div>

    <!-- 底部版权 -->
    <div class="copyright">
      © 2026 数据资产检索系统 · 江苏怀业
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis, User, Lock, InfoFilled } from '@element-plus/icons-vue'
import authApi from '../api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    const res = await authApi.login(form.username, form.password)
    
    // 保存Token和用户信息
    localStorage.setItem('token', res.token)
    localStorage.setItem('username', res.username)
    localStorage.setItem('role', res.role)
    
    ElMessage.success(`欢迎回来，${res.username}！`)
    
    // 使用location跳转强制刷新页面状态
    window.location.href = '/emergency'
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* =====================================================
   Glassmorphism Login Page
   紫蓝渐变背景 + 毛玻璃卡片
   ===================================================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
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
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 动态光效球 */
.background-effects {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #667eea 0%, transparent 70%);
  top: -200px;
  left: -100px;
  animation: float 8s ease-in-out infinite;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #764ba2 0%, transparent 70%);
  bottom: -150px;
  right: -100px;
  animation: float 10s ease-in-out infinite reverse;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-30px) rotate(5deg); }
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.4; }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.6; }
}

/* 玻璃态登录卡片 */
.login-card.glass-card {
  width: 420px;
  padding: 48px 40px;
  position: relative;
  z-index: 10;
  
  /* 玻璃态核心样式 */
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  
  /* 边框和圆角 */
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  
  /* 阴影和光效 */
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
}

/* 头部 */
.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-container {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 8px 24px rgba(102, 126, 234, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.logo-icon {
  color: white;
  font-size: 32px;
}

.login-header h1 {
  color: #FFFFFF;
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.login-header p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 15px;
  font-weight: 400;
}

/* 表单 */
.login-form {
  margin-bottom: 24px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-form-item__error) {
  color: #ff6b6b;
  padding-left: 44px;
}

/* 输入框包装 */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 16px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 18px;
  z-index: 2;
}

.glass-input {
  width: 100%;
}

.glass-input :deep(.el-input__wrapper) {
  width: 100%;
  height: 52px !important;
  padding: 0 16px 0 44px !important;
  border-radius: 14px !important;
  
  /* 玻璃态输入框 */
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.1) !important;
  
  transition: all 0.3s ease !important;
}

.glass-input :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.12) !important;
  border-color: rgba(255, 255, 255, 0.25) !important;
}

.glass-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: rgba(102, 126, 234, 0.6) !important;
  box-shadow: 
    0 0 0 3px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

.glass-input :deep(.el-input__inner) {
  height: 50px !important;
  line-height: 50px !important;
  font-size: 15px !important;
  color: #FFFFFF !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
}

.glass-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

.glass-input :deep(.el-input__suffix) {
  color: rgba(255, 255, 255, 0.6);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 52px !important;
  border: none !important;
  border-radius: 14px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: 4px;
  font-family: 'Inter', -apple-system, sans-serif !important;
  
  /* 渐变按钮 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  
  transition: all 0.3s ease !important;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 24px rgba(102, 126, 234, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.login-btn:active {
  transform: translateY(0);
}

/* 底部提示 */
.login-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.hint-box {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.hint-box .el-icon {
  color: rgba(102, 126, 234, 0.8);
}

/* 版权信息 */
.copyright {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  z-index: 10;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card.glass-card {
    width: calc(100% - 32px);
    padding: 36px 24px;
    margin: 16px;
  }
  
  .gradient-orb {
    display: none;
  }
}
</style>
