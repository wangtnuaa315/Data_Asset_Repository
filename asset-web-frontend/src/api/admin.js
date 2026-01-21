/**
 * admin.js - 管理员API
 */
import axios from 'axios'
import authApi from './auth'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://192.168.2.170:8000'

const adminApi = {
    /**
     * 获取文件列表
     */
    async listFiles(subdir = '') {
        const response = await axios.get(`${API_BASE}/admin/files`, {
            params: { subdir },
            headers: authApi.getAuthHeaders()
        })
        return response.data
    },

    /**
     * 上传文件
     */
    async uploadFile(file, subdir = '') {
        const formData = new FormData()
        formData.append('file', file)
        if (subdir) {
            formData.append('subdir', subdir)
        }

        const response = await axios.post(`${API_BASE}/admin/upload`, formData, {
            headers: {
                ...authApi.getAuthHeaders(),
                'Content-Type': 'multipart/form-data'
            }
        })
        return response.data
    },

    /**
     * 上传文件（带进度）
     */
    async uploadFileWithProgress(file, subdir = '', onProgress) {
        const formData = new FormData()
        formData.append('file', file)
        if (subdir) {
            formData.append('subdir', subdir)
        }

        const response = await axios.post(`${API_BASE}/admin/upload`, formData, {
            headers: {
                ...authApi.getAuthHeaders(),
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const percent = (progressEvent.loaded * 100) / progressEvent.total
                    onProgress(percent)
                }
            }
        })
        return response.data
    },

    /**
     * 删除文件
     */
    async deleteFile(path) {
        const response = await axios.delete(`${API_BASE}/admin/files`, {
            data: { path },
            headers: authApi.getAuthHeaders()
        })
        return response.data
    },

    /**
     * 创建目录
     */
    async createDirectory(name) {
        const response = await axios.post(`${API_BASE}/admin/directories`,
            { name },
            { headers: authApi.getAuthHeaders() }
        )
        return response.data
    },

    /**
     * 获取脚本列表
     */
    async listScripts() {
        const response = await axios.get(`${API_BASE}/admin/scripts/list`, {
            headers: authApi.getAuthHeaders()
        })
        return response.data
    },

    /**
     * 执行脚本
     */
    async runScript(scriptId) {
        const response = await axios.post(`${API_BASE}/admin/scripts/run`,
            { script: scriptId },
            { headers: authApi.getAuthHeaders() }
        )
        return response.data
    }
}

export default adminApi
