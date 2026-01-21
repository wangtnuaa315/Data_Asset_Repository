<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="48" class="logo-icon"><DataAnalysis /></el-icon>
        <h1>数据资产检索系统</h1>
        <p>请登录以继续</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p class="hint">
          <el-icon><InfoFilled /></el-icon>
          普通用户：user / user123
        </p>
      </div>
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
   Bento Grids / Apple Style + AI 科技背景
   米白背景 + 圆角卡片 + 柔和阴影
   ===================================================== */

/* Google Fonts - Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Apple 风格米白背景 + 渐变光球 */
  background: #F5F5F7;
  background-image:
    /* 左上角 - 蓝色光晕 */
    radial-gradient(600px circle at 10% 20%,
      rgba(0, 122, 255, 0.12) 0%,
      transparent 50%),
    /* 右下角 - 紫色光晕 */
    radial-gradient(500px circle at 90% 80%,
      rgba(88, 86, 214, 0.1) 0%,
      transparent 50%),
    /* 中间 - 淡粉色光晕 */
    radial-gradient(400px circle at 50% 50%,
      rgba(255, 45, 85, 0.05) 0%,
      transparent 50%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;
}

/* AI 科技背景图 */
.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/ai_bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
  opacity: 0.6;
}

/* 移除旧的伪元素 */
.login-container::after {
  display: none;
}

/* Bento 风格登录卡片 */
.login-card {
  width: 420px;
  padding: 48px;
  /* 完全不透明白色卡片 */
  background: #FFFFFF;
  /* 大圆角 - Apple 风格 */
  border-radius: 24px;
  /* 更强的阴影 - 从背景中凸显 */
  box-shadow:
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 20px rgba(0, 0, 0, 0.08),
    0 20px 40px rgba(0, 0, 0, 0.1);
  /* 确保在背景之上 */
  position: relative;
  z-index: 10;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

/* Logo - Apple 风格渐变 */
.logo-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.25);
  color: white;
  padding: 0;
  border: none;
}

.login-header h1 {
  color: #1D1D1F;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
  font-family: 'Inter', -apple-system, sans-serif;
}

.login-header p {
  color: #86868B;
  font-size: 15px;
  font-weight: 400;
}

.login-form {
  margin-bottom: 32px;
}

/* Element Plus 输入框样式覆盖 */
.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-form-item__label) {
  color: #1D1D1F;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Inter', -apple-system, sans-serif;
}

.login-form :deep(.el-input__wrapper) {
  height: 52px !important;
  border-radius: 12px !important;
  border: 1px solid #D2D2D7 !important;
  box-shadow: none !important;
  padding: 0 16px !important;
  background: #FFFFFF !important;
  transition: all 0.2s ease !important;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: #86868B !important;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #007AFF !important;
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1) !important;
}

.login-form :deep(.el-input__inner) {
  height: 50px !important;
  line-height: 50px !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  font-size: 16px !important;
  color: #1D1D1F !important;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #86868B !important;
}

.login-form :deep(.el-input__prefix) {
  color: #86868B;
}

/* Apple 蓝色登录按钮 */
.login-btn {
  width: 100%;
  height: 52px !important;
  border: none !important;
  border-radius: 12px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  background: #007AFF !important;
  color: white !important;
  transition: all 0.2s ease !important;
}

.login-btn:hover {
  background: #0066CC !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.login-footer {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #E8E8ED;
}

.hint {
  color: #86868B;
  font-size: 13px;
  font-family: 'Inter', -apple-system, sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.hint strong {
  color: #1D1D1F;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    width: calc(100% - 32px);
    padding: 32px 24px;
    margin: 16px;
  }
}
</style>
