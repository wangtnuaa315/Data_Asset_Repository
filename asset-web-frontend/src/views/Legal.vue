<template>
  <div class="legal-page">
    <!-- 搜索区域 -->
    <div class="search-section">
      <!-- 第一行：关键词搜索 -->
      <div class="search-row">
        <el-input
          v-model="searchForm.keyword"
          placeholder="输入案由、标题关键词搜索..."
          clearable
          class="keyword-input"
          @keyup.enter="handleSearchClick"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" :icon="Search" @click="handleSearchClick" :loading="loading">
          检索
        </el-button>
        <el-button :icon="Refresh" @click="handleReset">
          重置
        </el-button>
      </div>
      
      <!-- 第二行：筛选条件（均分宽度） -->
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">案件类型</span>
          <el-select
            v-model="searchForm.case_type"
            placeholder="全部"
            clearable
            @change="handleCaseTypeChange"
          >
            <el-option v-for="item in caseTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">案由</span>
          <el-cascader
            v-model="selectedCausePath"
            :options="causeTreeOptions"
            :props="cascaderProps"
            placeholder="从分类中选择"
            clearable
            filterable
            @change="handleCauseChange"
          />
        </div>

        <div class="filter-item">
          <span class="filter-label">地域</span>
          <el-select
            v-model="searchForm.region"
            placeholder="全部"
            clearable
            filterable
          >
            <el-option v-for="item in regions" :key="item" :label="item" :value="item" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">程序</span>
          <el-select
            v-model="searchForm.trial_procedure"
            placeholder="全部"
            clearable
          >
            <el-option v-for="item in trialProcedures" :key="item" :label="item" :value="item" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">年份</span>
          <div class="year-range">
            <el-select v-model="searchForm.judgment_year_start" placeholder="起" clearable>
              <el-option v-for="year in yearOptions" :key="year" :label="year + '年'" :value="year" />
            </el-select>
            <span class="year-sep">-</span>
            <el-select v-model="searchForm.judgment_year_end" placeholder="止" clearable>
              <el-option v-for="year in yearOptions" :key="year" :label="year + '年'" :value="year" />
            </el-select>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果统计 -->
    <div v-if="documentList.length > 0" class="results-header">
      <div class="stats">
        <el-icon><Document /></el-icon>
        <span>找到 <strong>{{ total }}</strong> 份法律文书</span>
      </div>
    </div>

    <!-- 文书列表 -->
    <div v-if="documentList.length > 0" class="results-list">
      <el-table
        :data="documentList"
        v-loading="loading"
        row-key="doc_id"
        class="document-table"
        @row-click="showDocumentDetail"
        style="width: 100%"
      >
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />

        <el-table-column prop="case_cause" label="案由" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag effect="plain" size="small">{{ row.case_cause }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.case_type)" effect="dark" size="small">
              {{ row.case_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="trial_procedure" label="程序" width="80" />
        <el-table-column prop="region" label="地域" width="100" show-overflow-tooltip />
        <el-table-column prop="judgment_year" label="年份" width="80" />
        <el-table-column prop="judgment_result" label="结果" min-width="120" show-overflow-tooltip />
      </el-table>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="hasSearched && !loading && documentList.length === 0"
      description="未找到匹配的法律文书"
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

    <!-- 文书详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="文书详情"
      width="800px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div class="dialog-scroll-content">
      <div v-if="currentDocument" class="document-detail">
        <!-- 头部信息 -->
        <div class="detail-header">
          <div class="detail-title">{{ currentDocument.title }}</div>
          <div class="detail-meta">
            <el-tag :type="getTagType(currentDocument.case_type)" effect="plain">
              {{ currentDocument.case_type }}
            </el-tag>
            <span class="meta-item">{{ currentDocument.case_cause }}</span>
            <span class="meta-item">{{ currentDocument.trial_procedure }}</span>
            <span class="meta-item">{{ currentDocument.region }}</span>
            <span class="meta-item">{{ currentDocument.judgment_year }}年</span>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="info-grid">
          <div class="info-item" v-if="currentDocument.judgment_result">
            <span class="info-label">裁判结果</span>
            <span class="info-value highlight">{{ currentDocument.judgment_result }}</span>
          </div>
          <div class="info-item" v-if="currentDocument.claim_amount">
            <span class="info-label">诉请金额</span>
            <span class="info-value">¥ {{ formatAmount(currentDocument.claim_amount) }}</span>
          </div>
          <div class="info-item" v-if="currentDocument.judgment_amount">
            <span class="info-label">判决金额</span>
            <span class="info-value">¥ {{ formatAmount(currentDocument.judgment_amount) }}</span>
          </div>
          <div class="info-item" v-if="currentDocument.fine_amount">
            <span class="info-label">罚金</span>
            <span class="info-value">¥ {{ formatAmount(currentDocument.fine_amount) }}</span>
          </div>
        </div>

        <!-- 裁判结果段 -->
        <div v-if="currentDocument.judgment_section" class="content-section">
          <div class="section-title">裁判结果</div>
          <div class="section-content">{{ currentDocument.judgment_section }}</div>
        </div>

        <!-- 裁判理由段 -->
        <div v-if="currentDocument.reasoning_section" class="content-section">
          <div class="section-title">裁判理由</div>
          <div class="section-content">{{ currentDocument.reasoning_section }}</div>
        </div>

        <!-- 引用法条 -->
        <div v-if="currentDocument.cited_laws" class="content-section">
          <div class="section-title">引用法条</div>
          <div class="section-content laws">{{ currentDocument.cited_laws }}</div>
        </div>
      </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Document } from '@element-plus/icons-vue'
import {
  searchDocuments,
  getDocumentDetail,
  getCauseTree,
  getCauseDescendants,
  getRegions,
  getTrialProcedures
} from '../api/legal'

// 搜索表单
const searchForm = reactive({
  keyword: '',
  case_type: '',
  case_causes: null,
  trial_procedure: '',
  region: '',
  judgment_year_start: null,
  judgment_year_end: null,
  judgment_result: ''
})

// 状态
const loading = ref(false)
const hasSearched = ref(false)

// 数据
const documentList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选选项
const caseTypes = ref(['民事', '刑事', '行政', '赔偿'])
const regions = ref([])
const trialProcedures = ref([])
const causeTree = ref([])
const selectedCausePath = ref([])

// 详情弹窗
const detailVisible = ref(false)
const currentDocument = ref(null)

// 年份选项
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let y = currentYear; y >= 2010; y--) {
    years.push(y)
  }
  return years
})

// 级联选择器配置
const cascaderProps = {
  value: 'id',
  label: 'cause_name',
  children: 'children',
  checkStrictly: true,
  emitPath: true
}

// 将案由树转换为级联选择器格式
const causeTreeOptions = computed(() => {
  return causeTree.value
})

// 初始化
onMounted(async () => {
  try {
    const [regionsData, proceduresData, treeData] = await Promise.all([
      getRegions(),
      getTrialProcedures(),
      getCauseTree()
    ])
    regions.value = regionsData
    trialProcedures.value = proceduresData
    causeTree.value = treeData
  } catch (e) {
    console.error('加载筛选选项失败:', e)
  }
})

// 案件类型变化时重新加载案由树
const handleCaseTypeChange = async () => {
  selectedCausePath.value = []
  searchForm.case_causes = null
  
  if (searchForm.case_type) {
    try {
      causeTree.value = await getCauseTree(searchForm.case_type)
    } catch (e) {
      console.error('加载案由树失败:', e)
    }
  } else {
    causeTree.value = await getCauseTree()
  }
}

// 案由选择变化
const handleCauseChange = async (value) => {
  if (value && value.length > 0) {
    const selectedId = value[value.length - 1]
    try {
      searchForm.case_causes = await getCauseDescendants(selectedId)
    } catch (e) {
      console.error('获取子孙案由失败:', e)
    }
  } else {
    searchForm.case_causes = null
  }
}

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
    const result = await searchDocuments({
      ...searchForm,
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    documentList.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error('检索失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 重置
const handleReset = async () => {
  searchForm.keyword = ''
  searchForm.case_type = ''
  searchForm.case_causes = null
  searchForm.trial_procedure = ''
  searchForm.region = ''
  searchForm.judgment_year_start = null
  searchForm.judgment_year_end = null
  searchForm.judgment_result = ''
  selectedCausePath.value = []
  currentPage.value = 1
  documentList.value = []
  total.value = 0
  hasSearched.value = false
  
  causeTree.value = await getCauseTree()
}

// 显示文书详情
const showDocumentDetail = async (row) => {
  try {
    currentDocument.value = await getDocumentDetail(row.doc_id)
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('获取文书详情失败')
  }
}

// 辅助函数
const getTagType = (type) => {
  const map = { '民事': 'warning', '刑事': 'danger', '行政': 'info', '赔偿': 'success' }
  return map[type] || ''
}

const formatAmount = (amount) => {
  return amount ? Number(amount).toLocaleString() : '-'
}
</script>

<style scoped>
/* =====================================================
   与 Emergency.vue 一致的布局
   ===================================================== */

.legal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 搜索区域 */
.search-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 24px;
  width: 100%;
  background: #FFFFFF;
  border-radius: 20px;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 第一行：关键词 + 按钮 */
.search-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.keyword-input {
  flex: 1;
}

/* 第二行：筛选条件均分 */
.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item .filter-label {
  font-size: 13px;
  color: #86868B;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-item .el-select,
.filter-item .el-cascader {
  flex: 1;
  min-width: 0;
}

.year-range {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.year-range .el-select {
  flex: 1;
  min-width: 0;
}

.year-sep {
  color: #86868B;
  font-size: 13px;
  flex-shrink: 0;
}

/* Apple 风格输入框 */
.search-section :deep(.el-input__wrapper),
.search-section :deep(.el-select__wrapper) {
  height: 44px !important;
  border-radius: 10px !important;
  padding: 0 12px !important;
  border: 1px solid #D2D2D7 !important;
  box-shadow: none !important;
  background: #FFFFFF !important;
}

.search-section :deep(.el-input__wrapper.is-focus),
.search-section :deep(.el-select__wrapper.is-focus) {
  border-color: #007AFF !important;
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1) !important;
}

.search-section :deep(.el-input__inner) {
  height: 42px !important;
  font-size: 14px !important;
}

.search-section :deep(.el-button--primary) {
  background: #007AFF !important;
  border-color: #007AFF !important;
  border-radius: 10px !important;
  height: 44px !important;
  font-weight: 600 !important;
  padding: 0 20px !important;
}

.search-section :deep(.el-button:not(.el-button--primary)) {
  border-radius: 10px !important;
  height: 44px !important;
}

.keyword-input {
  width: 100%;
}

.compact-select {
  width: 120px !important;
}

.small-select {
  width: 90px !important;
}

.cause-cascader {
  width: 200px;
}

.cause-cascader :deep(.el-input__wrapper) {
  height: 48px !important;
  border-radius: 12px !important;
  border: 1px solid #D2D2D7 !important;
  box-shadow: none !important;
}

.year-sep {
  color: #86868B;
  font-size: 13px;
  margin: 0 4px;
}

.search-actions-inline {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.search-section :deep(.el-button--primary) {
  background: #007AFF !important;
  border-color: #007AFF !important;
  border-radius: 12px !important;
  height: 48px !important;
  font-weight: 600 !important;
  padding: 0 24px !important;
}

.search-section :deep(.el-button:not(.el-button--primary)) {
  border-radius: 12px !important;
  height: 48px !important;
}

/* 结果统计 - 与 Emergency 一致 */
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stats {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #86868B;
  font-size: 14px;
}

.stats strong {
  color: #007AFF;
  font-size: 18px;
  font-weight: 600;
}

/* 列表视图 - 与 Emergency 一致 */
.results-list {
  flex: 1;
  min-height: 0;
  border-radius: 16px;
  overflow: auto;
  background: #FFFFFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* 表格样式 */
.document-table {
  width: 100% !important;
}

.document-table :deep(th.el-table__cell) {
  background: #F8F8FA !important;
  color: #1D1D1F;
  font-weight: 600;
  border-bottom: 1px solid #E5E5E5;
  height: 52px;
}

.document-table :deep(.el-table__row) {
  cursor: pointer;
}

.document-table :deep(.el-table__row:hover > td) {
  background: rgba(0, 122, 255, 0.04) !important;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* 详情弹窗 - 高度限制，内容滚动 */
.dialog-scroll-content {
  max-height: 50vh;
  overflow-y: auto;
  padding-right: 8px;
}

.dialog-scroll-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-scroll-content::-webkit-scrollbar-thumb {
  background: #D2D2D7;
  border-radius: 3px;
}

.dialog-scroll-content::-webkit-scrollbar-thumb:hover {
  background: #007AFF;
}

.detail-header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #F2F2F5;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 12px;
  line-height: 1.4;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 13px;
  color: #86868B;
}

.meta-item::before {
  content: '•';
  margin-right: 12px;
  color: #D2D2D7;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #86868B;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #1D1D1F;
  font-weight: 500;
}

.info-value.highlight {
  color: #007AFF;
}

.content-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background: #007AFF;
  border-radius: 2px;
}

.section-content {
  font-size: 14px;
  color: #1D1D1F;
  line-height: 1.8;
  background: #F8F8FA;
  padding: 16px;
  border-radius: 12px;
  white-space: pre-wrap;
}

.section-content.laws {
  font-family: 'SF Mono', monospace;
  font-size: 13px;
  color: #007AFF;
}

/* 弹窗层级修复 */
:deep(.detail-dialog) {
  z-index: 3000 !important;
}

:deep(.el-overlay) {
  z-index: 2999 !important;
}
</style>
