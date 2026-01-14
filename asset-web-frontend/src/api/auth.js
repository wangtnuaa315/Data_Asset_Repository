/**
 * auth.js - 认证API
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://192.168.2.170:8000'

const authApi = {
    /**
     * 用户登录
     */
    async login(username, password) {
        const response = await axios.post(`${API_BASE}/auth/login`, {
            username,
            password
        })
        return response.data
    },

    /**
     * 用户登出
     */
    async logout() {
        const response = await axios.post(`${API_BASE}/auth/logout`)
        // 清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        localStorage.removeItem('role')
        return response.data
    },

    /**
     * 获取当前用户信息
     */
    getCurrentUser() {
        return {
            username: localStorage.getItem('username'),
            role: localStorage.getItem('role'),
            token: localStorage.getItem('token')
        }
    },

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!localStorage.getItem('token')
    },

    /**
     * 检查是否为管理员
     */
    isAdmin() {
        return localStorage.getItem('role') === 'admin'
    },

    /**
     * 获取带Token的请求头
     */
    getAuthHeaders() {
        const token = localStorage.getItem('token')
        return token ? { Authorization: `Bearer ${token}` } : {}
    }
}

export default authApi
