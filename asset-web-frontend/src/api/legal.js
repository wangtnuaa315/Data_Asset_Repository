/**
 * 法律文书模块 API
 */
import axios from 'axios'

const API_BASE = '/api/legal'

/**
 * 检索法律文书
 * @param {Object} params - 搜索参数
 */
export async function searchDocuments(params) {
  const response = await axios.post(`${API_BASE}/documents/search`, {
    keyword: params.keyword || null,
    case_type: params.case_type || null,
    case_causes: params.case_causes || null,
    trial_procedure: params.trial_procedure || null,
    region: params.region || null,
    judgment_year_start: params.judgment_year_start || null,
    judgment_year_end: params.judgment_year_end || null,
    judgment_result: params.judgment_result || null,
    page: params.page || 1,
    page_size: params.page_size || 20
  })
  return response.data
}

/**
 * 获取文书详情
 * @param {string} docId - 文书ID
 */
export async function getDocumentDetail(docId) {
  const response = await axios.get(`${API_BASE}/documents/${docId}`)
  return response.data
}

/**
 * 获取案由树形结构
 * @param {string} caseType - 可选，按案件类型筛选
 */
export async function getCauseTree(caseType) {
  const params = caseType ? { case_type: caseType } : {}
  const response = await axios.get(`${API_BASE}/cause-tree`, { params })
  return response.data.items
}

/**
 * 获取某节点下所有子孙案由
 * @param {number} parentId - 父节点ID
 */
export async function getCauseDescendants(parentId) {
  const response = await axios.get(`${API_BASE}/cause-descendants/${parentId}`)
  return response.data.items
}

/**
 * 获取案由统计（从实际数据中）
 * @param {string} caseType - 可选
 */
export async function getCauseStats(caseType) {
  const params = caseType ? { case_type: caseType } : {}
  const response = await axios.get(`${API_BASE}/cause-stats`, { params })
  return response.data.items
}

/**
 * 获取地域列表
 */
export async function getRegions() {
  const response = await axios.get(`${API_BASE}/regions`)
  return response.data.items
}

/**
 * 获取审理程序列表
 */
export async function getTrialProcedures() {
  const response = await axios.get(`${API_BASE}/trial-procedures`)
  return response.data.items
}

/**
 * 获取裁判结果列表
 */
export async function getJudgmentResults() {
  const response = await axios.get(`${API_BASE}/judgment-results`)
  return response.data.items
}

/**
 * 获取裁判年份范围
 */
export async function getJudgmentYears() {
  const response = await axios.get(`${API_BASE}/judgment-years`)
  return response.data
}

/**
 * 获取案件类型列表
 */
export async function getCaseTypes() {
  const response = await axios.get(`${API_BASE}/case-types`)
  return response.data.items
}
