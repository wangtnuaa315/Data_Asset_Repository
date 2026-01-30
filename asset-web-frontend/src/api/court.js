/**
 * 法院卷宗模块 API
 */
import axios from 'axios'

const API_BASE = '/api/court'

/**
 * 检索案件列表
 * @param {Object} params - 搜索参数
 */
export async function searchCases(params) {
    const response = await axios.post(`${API_BASE}/cases/search`, {
        ah: params.ah || null,
        ay_ms: params.ay_ms || null,
        ajlx_mc: params.ajlx_mc || null,
        trial_stage: params.trial_stage || null,
        cbr_mc: params.cbr_mc || null,
        region: params.region || null,
        dossier_categories: params.dossier_categories && params.dossier_categories.length > 0
            ? params.dossier_categories : null,
        start_date: params.start_date || null,
        end_date: params.end_date || null,
        keyword: params.keyword || null,
        page: params.page || 1,
        page_size: params.page_size || 20
    })
    return response.data
}

/**
 * 获取所有区域列表（动态从数据库获取）
 */
export async function getRegions() {
    const response = await axios.get(`${API_BASE}/regions`)
    return response.data.regions
}

/**
 * 获取案件详情
 * @param {string} caseCode - 案件编码
 */
export async function getCaseDetail(caseCode) {
    const response = await axios.get(`${API_BASE}/cases/${caseCode}`)
    return response.data
}

/**
 * 获取案件卷宗列表
 * @param {string} caseCode - 案件编码
 */
export async function getCaseDossiers(caseCode) {
    const response = await axios.get(`${API_BASE}/cases/${caseCode}/dossiers`)
    return response.data
}

/**
 * 获取卷宗预览URL（浏览器内显示）
 * @param {string} dossierCode - 卷宗编码
 */
export function getDossierPreviewUrl(dossierCode) {
    return `${API_BASE}/dossiers/${encodeURIComponent(dossierCode)}/preview`
}

/**
 * 获取卷宗下载URL
 * @param {string} dossierCode - 卷宗编码
 */
export function getDossierDownloadUrl(dossierCode) {
    return `${API_BASE}/dossiers/${dossierCode}/download`
}

/**
 * 下载卷宗文件
 * @param {string} dossierCode - 卷宗编码
 * @param {string} filename - 文件名
 */
export async function downloadDossier(dossierCode, filename) {
    const url = getDossierDownloadUrl(dossierCode)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

/**
 * 获取案件类型列表
 */
export async function getCaseTypes() {
    const response = await axios.get(`${API_BASE}/case-types`)
    return response.data.items
}

/**
 * 获取案由列表
 */
export async function getCaseReasons() {
    const response = await axios.get(`${API_BASE}/case-reasons`)
    return response.data.items
}

/**
 * 获取卷宗分类列表
 */
export async function getDossierCategories() {
    const response = await axios.get(`${API_BASE}/dossier-categories`)
    return response.data.items
}

/**
 * 按分类搜索卷宗
 * @param {Object} params - 搜索参数
 * @param {Array} params.category_ids - 分类ID列表
 * @param {string} params.case_code - 案件编号
 * @param {string} params.keyword - 关键词
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export async function searchDossiersByCategory(params) {
    const queryParams = new URLSearchParams()

    if (params.category_ids && params.category_ids.length > 0) {
        queryParams.append('category_ids', params.category_ids.join(','))
    }
    if (params.case_code) {
        queryParams.append('case_code', params.case_code)
    }
    if (params.keyword) {
        queryParams.append('keyword', params.keyword)
    }
    queryParams.append('page', params.page || 1)
    queryParams.append('page_size', params.page_size || 20)

    const response = await axios.get(`${API_BASE}/dossiers/search?${queryParams.toString()}`)
    return response.data
}

/**
 * 获取分类统计
 */
export async function getCategoryStats() {
    const response = await axios.get(`${API_BASE}/dossiers/category-stats`)
    return response.data.items
}

/**
 * 获取案件卷宗 ZIP 打包下载 URL
 * @param {string} caseCode - 案件编号
 */
export function getCaseZipDownloadUrl(caseCode) {
    return `${API_BASE}/cases/${encodeURIComponent(caseCode)}/download-zip`
}
