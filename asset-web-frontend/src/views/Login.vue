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
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Light Glassmorphism 渐变背景 */
  background: linear-gradient(135deg, #F8FAFC 0%, #E0F2FE 50%, #DBEAFE 100%);
  position: relative;
  overflow: hidden;
}

/* 科技线条背景纹理 */
.login-container::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg stroke='%233B82F6' stroke-opacity='0.06' stroke-width='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  pointer-events: none;
}

/* 渐变光晕装饰 */
.login-container::after {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
  top: -100px;
  right: -100px;
  pointer-events: none;
}

/* 磨砂玻璃登录卡片 */
.login-card {
  width: 420px;
  padding: 48px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  z-index: 10;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

/* 渐变蓝色 Logo 图标 */
.logo-icon {
  color: #fff;
  background: var(--gradient-primary);
  padding: 14px;
  border-radius: 14px;
  margin-bottom: 20px;
  width: 60px;
  height: 60px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.35);
}

.login-header h1 {
  font-family: var(--font-heading);
  color: var(--text-primary);
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 32px;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px !important;
}

.login-footer {
  text-align: center;
}

.hint {
  color: var(--text-muted);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
</style>
