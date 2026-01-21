<template>
  <div class="court-page">
    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-compact-wrapper">
        <el-form :model="searchForm" class="search-form-flex" :inline="true">
          <!-- 案号 -->
          <el-form-item label="案号" class="compact-item">
            <el-input 
              v-model="searchForm.ah" 
              placeholder="输入案号" 
              clearable
              class="compact-input"
              @keyup.enter="handleSearchClick"
            />
          </el-form-item>

          <!-- 案由 -->
          <el-form-item label="案由" class="compact-item">
            <el-select
              v-model="searchForm.ay_ms"
              placeholder="选择案由"
              clearable
              filterable
              class="compact-input"
            >
              <el-option
                v-for="item in caseReasons"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>

          <!-- 案件类型 -->
          <el-form-item label="类型" class="compact-item small-item">
            <el-select
              v-model="searchForm.ajlx_mc"
              placeholder="全部"
              clearable
              class="compact-input"
            >
              <el-option label="民事" value="民事" />
              <el-option label="刑事" value="刑事" />
              <el-option label="行政" value="行政" />
            </el-select>
          </el-form-item>

          <!-- 审判阶段 -->
          <el-form-item label="阶段" class="compact-item small-item">
            <el-select
              v-model="searchForm.trial_stage"
              placeholder="全部"
              clearable
              class="compact-input"
            >
              <el-option label="一审" :value="1" />
              <el-option label="二审" :value="2" />
            </el-select>
          </el-form-item>

          <!-- 承办人 -->
          <el-form-item label="承办人" class="compact-item small-item">
            <el-input 
              v-model="searchForm.cbr_mc" 
              placeholder="法官" 
              clearable
              class="compact-input"
            />
          </el-form-item>

          <!-- 按钮组 -->
          <div class="search-actions-inline">
            <el-button type="primary" :icon="Search" @click="handleSearchClick" :loading="loading">
              检索
            </el-button>
            <el-button :icon="Refresh" @click="handleReset" class="reset-btn">
              重置
            </el-button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 结果统计 -->
    <div v-if="caseList.length > 0" class="results-header">
      <div class="stats">
        <el-icon><Folder /></el-icon>
        <span>找到 <strong>{{ total }}</strong> 个案件</span>
      </div>
      <div class="header-actions">
        <div class="selected-info" v-if="selectedCases.length > 0">
          <span>已选择 <strong>{{ selectedCases.length }}</strong> 个</span>
        </div>
        <el-button-group class="view-toggle">
          <el-button 
            :type="viewMode === 'list' ? 'primary' : 'default'" 
            :icon="List" 
            @click="viewMode = 'list'"
            title="列表视图"
          />
        </el-button-group>
      </div>
    </div>

    <!-- 案件列表表格 -->
    <div v-if="caseList.length > 0" class="results-container">
      <el-table
        :data="caseList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="case_code"
        class="case-table"
      >
        <el-table-column type="selection" width="45" />
        
        <el-table-column label="案号" min-width="200">
          <template #default="{ row }">
            <span class="case-number">{{ row.ah }}</span>
          </template>
        </el-table-column>

        <el-table-column label="案件名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.aj_mc }}
          </template>
        </el-table-column>

        <el-table-column label="案由" width="140">
          <template #default="{ row }">
            <el-tag :type="row.ajlx_mc === '刑事' ? 'danger' : 'warning'" effect="plain" size="small">
              {{ row.ay_ms }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="阶段" width="80">
          <template #default="{ row }">
            <span :class="['trial-stage', row.trial_stage === 1 ? 'first' : 'second']">
              {{ row.trial_stage === 1 ? '一审' : '二审' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="卷宗统计" width="180">
          <template #default="{ row }">
            <div class="dossier-tags">
              <span :class="['dossier-tag', row.has_indictment ? '' : 'missing']">起诉状</span>
              <span :class="['dossier-tag', row.has_defense ? '' : 'missing']">答辩状</span>
              <span :class="['dossier-tag', row.has_judgement ? '' : 'missing']">判决书</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="承办人" width="90">
          <template #default="{ row }">
            {{ row.cbr_mc }}
          </template>
        </el-table-column>
        
        <el-table-column label="立案日期" width="110">
          <template #default="{ row }">
            <span class="time-text">{{ row.larq }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-tooltip content="查看详情" placement="top">
                <div class="action-icon" @click="showCaseDetail(row)">
                  <el-icon><View /></el-icon>
                </div>
              </el-tooltip>
              <el-tooltip content="下载卷宗" placement="top">
                <div class="action-icon download">
                  <el-icon><Download /></el-icon>
                </div>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="hasSearched && !loading && caseList.length === 0"
      description="未找到匹配的案件"
      :image-size="200"
    />

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handleSearch"
        @size-change="handleSearch"
      />
    </div>

    <!-- 案件详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title=""
      width="780px"
      :close-on-click-modal="false"
    >
      <div v-if="currentCase" class="case-detail">
        <div class="case-detail-header">
          <div>
            <div class="case-detail-title">{{ currentCase.aj_mc }}</div>
            <div class="case-detail-ah">{{ currentCase.ah }}</div>
          </div>
          <el-tag :type="currentCase.ajlx_mc === '民事' ? 'warning' : 'danger'" size="large" effect="plain">
            {{ currentCase.ajlx_mc }}
          </el-tag>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">法院</span>
            <span class="info-value">{{ currentCase.fymc }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">案由</span>
            <span class="info-value">{{ currentCase.ay_ms }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">承办人</span>
            <span class="info-value">{{ currentCase.cbr_mc }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">立案日期</span>
            <span class="info-value">{{ currentCase.larq }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">审判阶段</span>
            <span class="info-value">{{ currentCase.trial_stage === 1 ? '一审' : '二审' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">标的金额</span>
            <span class="info-value">{{ currentCase.bdje ? `¥ ${currentCase.bdje.toLocaleString()}` : '-' }}</span>
          </div>
        </div>

        <!-- 关联案件 -->
        <div v-if="currentCase.first_instance_ah" class="related-section">
          <div class="section-title">关联案件</div>
          <div class="related-case" @click="jumpToRelatedCase(currentCase.first_instance_ah)">
            <span class="related-case-icon">🔗</span>
            <div class="related-case-info">
              <div class="related-case-label">一审案件</div>
              <div class="related-case-ah">{{ currentCase.first_instance_ah }}</div>
            </div>
            <el-button type="primary" link>跳转查看 →</el-button>
          </div>
        </div>

        <!-- 卷宗目录 -->
        <div class="section-title">卷宗目录</div>
        <div class="dossier-tree" v-loading="loadingDossiers">
          <template v-if="dossierTree.length > 0">
            <div v-for="node in dossierTree" :key="node.dossier_code">
              <div class="tree-item" :class="{ folder: node.is_folder }">
                <span class="tree-icon" :class="node.is_folder ? 'folder' : 'file'">
                  {{ node.is_folder ? '📁' : '📄' }}
                </span>
                <span class="tree-name">{{ node.name }}</span>
                <span v-if="node.category_name" class="tree-category">{{ node.category_name }}</span>
              </div>
              <div v-if="node.children && node.children.length > 0" class="tree-children">
                <div 
                  v-for="child in node.children" 
                  :key="child.dossier_code"
                  class="tree-item"
                  @click="previewDossier(child)"
                >
                  <span class="tree-icon file">📄</span>
                  <span class="tree-name">{{ child.name }}</span>
                  <span v-if="child.category_name" class="tree-category">{{ child.category_name }}</span>
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else description="暂无卷宗" :image-size="80" />
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false" class="reset-btn">关闭</el-button>
        <el-button type="primary">
          <el-icon style="margin-right: 6px;"><Download /></el-icon>
          下载全部卷宗
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, List, View, Folder } from '@element-plus/icons-vue'
import { searchCases, getCaseDossiers, getCaseReasons, getDossierPreviewUrl } from '../api/court'

// 搜索表单
const searchForm = reactive({
  ah: '',
  ay_ms: '',
  ajlx_mc: '',
  trial_stage: null,
  cbr_mc: ''
})

// 案由列表
const caseReasons = ref([])

// 状态
const loading = ref(false)
const hasSearched = ref(false)
const viewMode = ref('list')

// 数据
const caseList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedCases = ref([])

// 详情弹窗
const detailVisible = ref(false)
const currentCase = ref(null)
const dossierTree = ref([])
const loadingDossiers = ref(false)

// 初始化
onMounted(async () => {
  try {
    caseReasons.value = await getCaseReasons()
  } catch (e) {
    console.error('获取案由列表失败:', e)
  }
})

// 搜索（重置页码）
const handleSearchClick = () => {
  currentPage.value = 1
  handleSearch()
}

// 搜索
const handleSearch = async () => {
  loading.value = true
  hasSearched.value = true
  
  try {
    const result = await searchCases({
      ...searchForm,
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    caseList.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error('检索失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 重置
const handleReset = () => {
  searchForm.ah = ''
  searchForm.ay_ms = ''
  searchForm.ajlx_mc = ''
  searchForm.trial_stage = null
  searchForm.cbr_mc = ''
  currentPage.value = 1
  caseList.value = []
  total.value = 0
  hasSearched.value = false
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedCases.value = selection
}

// 显示案件详情
const showCaseDetail = async (row) => {
  currentCase.value = row
  detailVisible.value = true
  loadingDossiers.value = true
  
  try {
    const result = await getCaseDossiers(row.case_code)
    dossierTree.value = result.tree || []
  } catch (error) {
    ElMessage.error('获取卷宗列表失败')
    dossierTree.value = []
  } finally {
    loadingDossiers.value = false
  }
}

// 跳转关联案件
const jumpToRelatedCase = (ah) => {
  searchForm.ah = ah
  detailVisible.value = false
  handleSearchClick()
}

// 预览卷宗
const previewDossier = (node) => {
  if (node.download_url) {
    window.open(getDossierPreviewUrl(node.dossier_code), '_blank')
  }
}
</script>

<style scoped>
/* =====================================================
   Bento Grids / Apple Style - Court Page
   ===================================================== */

.court-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
  position: relative;
  z-index: 1;
  
  /* 背景图 - 与应急模块一致 */
  background: url('/ai_bg.png') no-repeat center center;
  background-size: cover;
}

/* =====================================================
   搜索区域 - Bento 白色卡片
   ===================================================== */
.search-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px;
  width: 100%;
  background: #FFFFFF;
  border-radius: 24px;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 20px rgba(0, 0, 0, 0.08);
}

.search-form-flex {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.search-form-flex .el-form-item {
  margin-bottom: 0;
  margin-right: 0;
  display: flex;
  align-items: center;
}

/* Apple 风格输入框 */
.search-section :deep(.el-input__wrapper),
.search-section :deep(.el-select__wrapper) {
  height: 48px !important;
  border-radius: 12px !important;
  padding: 0 16px !important;
  border: 1px solid #D2D2D7 !important;
  box-shadow: none !important;
  background: #FFFFFF !important;
  transition: all 0.2s ease !important;
}

.search-section :deep(.el-input__wrapper:hover),
.search-section :deep(.el-select__wrapper:hover) {
  border-color: #86868B !important;
}

.search-section :deep(.el-input__wrapper.is-focus),
.search-section :deep(.el-select__wrapper.is-focus) {
  border-color: #007AFF !important;
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1) !important;
}

.search-section :deep(.el-input__inner) {
  height: 46px !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  font-size: 15px !important;
  color: #1D1D1F !important;
}

.search-section :deep(.el-form-item__label) {
  color: #1D1D1F;
  font-weight: 500;
  font-family: 'Inter', -apple-system, sans-serif;
}

.compact-input {
  width: 160px !important;
}

.small-item .compact-input {
  width: 100px !important;
}

.search-actions-inline {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

/* Apple 蓝色按钮 */
.search-actions-inline :deep(.el-button--primary) {
  background: #007AFF !important;
  border-color: #007AFF !important;
  border-radius: 12px !important;
  height: 48px !important;
  font-weight: 600 !important;
  padding: 0 24px !important;
}

.search-actions-inline :deep(.el-button--primary:hover) {
  background: #0066CC !important;
  border-color: #0066CC !important;
}

.reset-btn {
  background: #F5F5F7 !important;
  border-color: #D2D2D7 !important;
  border-radius: 12px !important;
  height: 48px !important;
  color: #1D1D1F !important;
}

.reset-btn:hover {
  color: #007AFF !important;
  border-color: #007AFF !important;
  background: rgba(0, 122, 255, 0.08) !important;
}

/* =====================================================
   结果区域
   ===================================================== */
.results-header {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px;
}

.stats {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #86868B;
  font-size: 15px;
}

.stats strong {
  color: #007AFF;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.results-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  background: #FFFFFF;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 20px rgba(0, 0, 0, 0.08);
  flex: 1;
  overflow: auto;
}

/* 表格样式 */
.case-table {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #F2F2F5;
}

.case-table :deep(th.el-table__cell) {
  background: #F8F8FA !important;
  color: #1D1D1F;
  font-weight: 600;
  border-bottom: 1px solid #E5E5E5;
  height: 52px;
}

.case-table :deep(.el-table__row:hover > td) {
  background: rgba(0, 122, 255, 0.04) !important;
}

/* 案号 */
.case-number {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 13px;
  color: #007AFF;
  font-weight: 500;
}

/* 审判阶段 */
.trial-stage {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.trial-stage.first {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.trial-stage.second {
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
}

/* 卷宗统计标签 */
.dossier-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dossier-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(52, 199, 89, 0.1);
  color: #34C759;
  font-weight: 500;
}

.dossier-tag.missing {
  background: rgba(255, 59, 48, 0.1);
  color: #FF3B30;
  text-decoration: line-through;
}

/* 时间 */
.time-text {
  font-size: 13px;
  color: #86868B;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
}

.action-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #007AFF;
  background: rgba(0, 122, 255, 0.08);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-icon:hover {
  background: rgba(0, 122, 255, 0.15);
  transform: scale(1.05);
}

.action-icon.download {
  color: #34C759;
  background: rgba(52, 199, 89, 0.08);
}

.action-icon.download:hover {
  background: rgba(52, 199, 89, 0.15);
}

/* 分页 */
.pagination-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* =====================================================
   案件详情弹窗
   ===================================================== */
.case-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #F2F2F5;
}

.case-detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 8px;
}

.case-detail-ah {
  font-family: 'SF Mono', monospace;
  font-size: 14px;
  color: #007AFF;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: #86868B;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 15px;
  color: #1D1D1F;
  font-weight: 500;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: #007AFF;
  border-radius: 2px;
}

.related-section {
  margin-bottom: 28px;
}

.related-case {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background: rgba(0, 122, 255, 0.05);
  border: 1px solid rgba(0, 122, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.related-case:hover {
  background: rgba(0, 122, 255, 0.1);
}

.related-case-icon {
  margin-right: 14px;
  font-size: 22px;
}

.related-case-info {
  flex: 1;
}

.related-case-label {
  font-size: 12px;
  color: #86868B;
}

.related-case-ah {
  font-size: 14px;
  color: #007AFF;
  font-family: 'SF Mono', monospace;
}

/* 卷宗树 */
.dossier-tree {
  background: #F8F8FA;
  border-radius: 16px;
  padding: 16px;
  max-height: 280px;
  overflow-y: auto;
}

.tree-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.tree-item:hover {
  background: rgba(0, 122, 255, 0.08);
}

.tree-item.folder {
  font-weight: 500;
}

.tree-icon {
  margin-right: 12px;
  font-size: 20px;
}

.tree-icon.folder {
  color: #FF9500;
}

.tree-icon.file {
  color: #007AFF;
}

.tree-name {
  flex: 1;
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
}

.tree-category {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  font-weight: 500;
}

.tree-children {
  margin-left: 32px;
}
</style>
