import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 60000  // 批量下载可能需要更长时间
})

// 请求拦截器
api.interceptors.request.use(
    config => {
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 响应拦截器
api.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        console.error('API Error:', error)
        return Promise.reject(error)
    }
)

export default {
    // 搜索告警资产
    searchAlarms(params) {
        return api.post('/emergency/search', params)
    },

    // 获取告警类型列表
    getAlarmTypes() {
        return api.get('/emergency/alarm-types')
    },

    // 获取缩略图URL
    getThumbnailUrl(assetId) {
        return `/api/thumbnail/${assetId}`
    },

    // 获取下载URL
    getDownloadUrl(assetId) {
        return `/api/download/${assetId}`
    },

    // 批量下载（返回ZIP文件Blob）
    async batchDownload(assetIds) {
        const response = await axios.post('/api/download/batch',
            { asset_ids: assetIds },
            { responseType: 'blob' }
        )
        return response.data
    }
}
