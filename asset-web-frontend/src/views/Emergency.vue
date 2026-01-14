<template>
  <div class="emergency-page">
    <!-- 搜索区域 -->
    <!-- 搜索区域 -->
    <div class="search-section">
      <!-- 移除独立的header，将标题整合到表单或直接简化 -->
      <div class="search-compact-wrapper">
        <el-form :model="searchForm" class="search-form-flex" :inline="true">
          <!-- 告警类型 -->
          <el-form-item label="告警类型" class="compact-item">
            <el-select
              v-model="searchForm.alarm_types"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="全部类型"
              clearable
              class="compact-input"
            >
              <el-option
                v-for="type in alarmTypes"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
          </el-form-item>

          <!-- 时间范围 -->
          <el-form-item label="时间范围" class="compact-item">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="-"
              start-placeholder="开始"
              end-placeholder="结束"
              value-format="YYYY-MM-DD"
              :shortcuts="dateShortcuts"
              class="compact-date"
            />
          </el-form-item>

          <!-- 设备编码 -->
          <el-form-item label="设备" class="compact-item small-item">
             <el-input 
               v-model="searchForm.dev_code" 
               placeholder="ID" 
               clearable
               class="compact-input"
             />
          </el-form-item>

          <!-- 关键词 -->
          <el-form-item label="关键词" class="compact-item medium-item">
            <el-input 
              v-model="searchForm.keyword" 
              placeholder="AI分析..." 
              clearable
              class="compact-input"
              @keyup.enter="handleSearch"
            />
          </el-form-item>

          <!-- 按钮组 -->
          <div class="search-actions-inline">
            <el-button type="primary" :icon="Search" @click="handleSearch" :loading="loading">
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
    <div v-if="searchResults.length > 0" class="results-header">
      <div class="stats">
        <el-icon><Document /></el-icon>
        <span>找到 <strong>{{ total }}</strong> 个资产</span>
      </div>
      <div class="header-actions">
        <div class="selected-info" v-if="selectedAssets.length > 0">
          <span>已选择 <strong>{{ selectedAssets.length }}</strong> 个</span>
          <el-button size="small" type="success" @click="handleBatchDownload">
            批量下载
          </el-button>
        </div>
        <el-button-group class="view-toggle">
          <el-button 
            :type="viewMode === 'grid' ? 'primary' : 'default'" 
            :icon="Grid" 
            @click="viewMode = 'grid'"
            title="卡片视图"
          />
          <el-button 
            :type="viewMode === 'list' ? 'primary' : 'default'" 
            :icon="List" 
            @click="viewMode = 'list'"
            title="列表视图"
          />
        </el-button-group>
      </div>
    </div>

    <!-- 结果网格 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="60"><Loading /></el-icon>
      <p>正在加载...</p>
    </div>

    <!-- 卡片视图 -->
    <div v-else-if="searchResults.length > 0 && viewMode === 'grid'" class="results-grid">
      <AssetCard
        v-for="asset in searchResults"
        :key="asset.asset_id"
        :asset="asset"
        :selected="selectedAssets.includes(asset.asset_id)"
        @select="toggleSelect(asset.asset_id)"
        @view-detail="showDetail(asset)"
      />
    </div>

    <!-- 列表视图 -->
    <div v-else-if="searchResults.length > 0 && viewMode === 'list'" class="results-list">
      <el-table
        :data="searchResults"
        style="width: 100%"
        @selection-change="handleSelectionChange"
        row-key="asset_id"
        class="asset-table"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <el-image
              :src="row.thumbnail_url"
              fit="cover"
              class="table-thumbnail"
              style="cursor: default;"
            />
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="alarm_name" label="告警类型" width="150">
          <template #default="{ row }">
            <el-tag type="warning" effect="dark" size="small">{{ row.alarm_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alarm_time" label="告警时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.alarm_time) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetail(row)" size="small">详情</el-button>
            <el-button type="success" link @click="downloadAsset(row)" size="small">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty
      v-else-if="hasSearched && !loading"
      description="未找到匹配的资产"
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

    <!-- 详情弹窗 -->
    <DetailModal
      v-model="detailVisible"
      :asset="currentAsset"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document, Loading, Warning, Cpu, Aim, Refresh, Download, Grid, List } from '@element-plus/icons-vue'
import api from '../api/emergency'
import AssetCard from '../components/AssetCard.vue'
import DetailModal from '../components/DetailModal.vue'

// 日期快捷选项
const dateShortcuts = [
  { text: '最近一周', value: () => { const end = new Date(); const start = new Date(); start.setTime(start.getTime() - 3600 * 1000 * 24 * 7); return [start, end] } },
  { text: '最近一月', value: () => { const end = new Date(); const start = new Date(); start.setTime(start.getTime() - 3600 * 1000 * 24 * 30); return [start, end] } },
  { text: '最近三月', value: () => { const end = new Date(); const start = new Date(); start.setTime(start.getTime() - 3600 * 1000 * 24 * 90); return [start, end] } },
]

// 搜索表单
const searchForm = reactive({
  alarm_types: [],
  dev_code: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

const dateRange = ref([])
const loading = ref(false)
const hasSearched = ref(false)
const alarmTypes = ref([])

// 搜索结果
const searchResults = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 选中的资产
const selectedAssets = ref([])

// 视图模式：grid（卡片）或 list（列表）
const viewMode = ref('grid')

// 详情弹窗
const detailVisible = ref(false)
const currentAsset = ref(null)

// 加载告警类型
onMounted(async () => {
  try {
    const res = await api.getAlarmTypes()
    alarmTypes.value = res.types
  } catch (error) {
    ElMessage.error('加载告警类型失败')
  }
})

// 搜索
const handleSearch = async () => {
  loading.value = true
  hasSearched.value = true

  try {
    // 处理日期范围
    if (dateRange.value && dateRange.value.length === 2) {
      searchForm.start_date = dateRange.value[0]
      searchForm.end_date = dateRange.value[1]
    } else {
      searchForm.start_date = ''
      searchForm.end_date = ''
    }

    const params = {
      ...searchForm,
      page: currentPage.value,
      page_size: pageSize.value
    }

    const res = await api.searchAlarms(params)
    searchResults.value = res.data
    total.value = res.total
  } catch (error) {
    ElMessage.error('搜索失败')
    console.error(error)
    // 搜索失败时清空结果
    searchResults.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    alarm_types: [],
    dev_code: '',
    keyword: '',
    start_date: '',
    end_date: ''
  })
  dateRange.value = []
  searchResults.value = []
  total.value = 0
  currentPage.value = 1
  hasSearched.value = false
  selectedAssets.value = []
}

// 选择/取消选择
const toggleSelect = (assetId) => {
  const index = selectedAssets.value.indexOf(assetId)
  if (index > -1) {
    selectedAssets.value.splice(index, 1)
  } else {
    selectedAssets.value.push(assetId)
  }
}

// 查看详情
const showDetail = (asset) => {
  currentAsset.value = asset
  detailVisible.value = true
}

// 批量下载（打包成ZIP）
const handleBatchDownload = async () => {
  if (selectedAssets.value.length === 0) {
    ElMessage.warning('请先选择要下载的资产')
    return
  }

  try {
    ElMessage.info('正在打包文件，请稍候...')
    
    const blob = await api.batchDownload(selectedAssets.value)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `assets_${Date.now()}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(`成功下载 ${selectedAssets.value.length} 个文件`)
    selectedAssets.value = []  // 清空选中状态
  } catch (error) {
    console.error('批量下载失败:', error)
    ElMessage.error('批量下载失败，请重试')
  }
}

// 表格选择变化（列表视图）
const handleSelectionChange = (selection) => {
  selectedAssets.value = selection.map(item => item.asset_id)
}

// 格式化日期时间
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  // 将ISO格式转换为更易读的格式
  return dateStr.replace('T', ' ').substring(0, 19)
}

// 下载单个资产
const downloadAsset = (asset) => {
  const url = api.getDownloadUrl(asset.asset_id)
  window.open(url, '_blank')
}
</script>

<style scoped>
.emergency-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow: hidden; /* 由内部容器滚动 */
}

/* 搜索区域增强 - 极简紧凑版 Flex布局 */
/* =====================================================
   搜索区域 - Visual Polish 用户指定规范
   max-width: 1200px | 居中 | 56px 高度 | 16px 圆角
   ===================================================== */
.search-section {
  /* 布局约束 - 不要占满全宽 */
  max-width: 1200px;
  margin: 0 auto 16px auto;
  
  /* 内边距 */
  padding: 20px 32px;
  
  /* 强制 Glassmorphism */
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.07);
  
  /* 圆润现代 */
  border-radius: 16px;
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

/* 输入框增强 - 56px 高度, 16px 圆角 */
.search-section :deep(.el-input__wrapper),
.search-section :deep(.el-select__wrapper) {
  height: 56px !important;
  border-radius: 16px !important;
  padding: 0 20px !important;
}

.search-section :deep(.el-input__inner) {
  height: 54px !important;
  line-height: 54px !important;
}

/* 控件宽度控制 - 四个条件平均分配 */
.compact-input {
  width: 180px !important;
}

.compact-date {
  width: 180px !important;
}

/* 移除 small/medium 差异，统一宽度 */
.small-item .compact-input {
  width: 140px !important;
}

.medium-item .compact-input {
  width: 180px !important;
}

.search-actions-inline {
  display: flex;
  gap: 8px;
  margin-left: auto; /* 推到右侧，如需紧挨则去掉此行 */
}

/* 移除不需要的header样式 */
.search-header, .header-title, .header-decoration, .search-section::after {
  display: none;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .search-actions-inline {
    margin-left: 0; /* 小屏幕下不强推右侧 */
  }
}

.reset-btn {
  background: #f8f9fa;
  border-color: #dcdfe6;
}

.reset-btn:hover {
  color: var(--primary-color);
  border-color: #b3d8ff;
  background-color: #ecf5ff;
}

/* 结果统计栏 - 磨砂玻璃 */
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  /* Glass Effect */
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  margin-top: 12px;
}

.stats, .selected-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
}

.stats strong, .selected-info strong {
  color: var(--primary-color);
  font-size: 18px;
  font-weight: 600;
  text-shadow: none;
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: var(--primary-color);
  text-shadow: 0 0 10px rgba(0, 242, 255, 0.4);
}

/* 结果网格 - 添加动画 */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  grid-auto-rows: 290px; /* 强制固定行高，防止卡片塌陷 */
  gap: 24px;
  padding-bottom: 20px;
  animation: fadeIn 0.5s ease-out;
  flex: 1;
  overflow-y: auto;
  min-height: 0; /* 允许flex子项滚动 */
  padding-right: 4px; /* 防止滚动条遮挡 */
}

/* 列表视图容器 */
.results-list {
  flex: 1;
  min-height: 0;
  border-radius: 8px;
  overflow: auto;
  background: #ffffff;
  border: 1px solid var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 表格轻量化适配 */
:deep(.asset-table) {
  --el-table-border-color: #ebeef5;
  --el-table-header-bg-color: #f8f9fa;
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-text-color: var(--text-regular);
  --el-table-header-text-color: var(--text-primary);
  --el-table-row-hover-bg-color: #f5f7fa;
}

:deep(.el-table__inner-wrapper::before) {
  background-color: #ebeef5;
}

:deep(.el-table td.el-table__cell),
:deep(.el-table th.el-table__cell) {
  border-bottom: 1px solid #ebeef5 !important;
}

:deep(.el-table th.el-table__cell) {
  font-weight: 600;
  letter-spacing: 1px;
}

/* 表格缩略图 */
.table-thumbnail {
  width: 80px;
  height: 50px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid rgba(0, 242, 255, 0.2);
  transition: all 0.3s ease;
}

.table-thumbnail:hover {
  border-color: var(--primary-color);
}

/* 暂无分析样式 */
.no-analysis {
  color: var(--text-muted);
  font-style: italic;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  flex-shrink: 0;
}

/* 分页组件深色主题适配 */
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: rgba(255, 255, 255, 0.05);
  --el-pagination-button-disabled-bg-color: transparent;
  --el-pagination-hover-color: var(--primary-color);
}

:deep(.el-pagination .el-select .el-input .el-input__wrapper) {
  background-color: rgba(0, 0, 0, 0.2) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

:deep(.el-pagination .el-pager li) {
  background: #ffffff !important;
  color: var(--text-secondary) !important;
  border: 1px solid #dcdfe6;
  margin: 0 4px;
  border-radius: 4px;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--primary-color) !important;
  color: #fff !important;
  font-weight: bold;
  border-color: var(--primary-color);
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background: #fff !important;
  color: var(--text-secondary) !important;
  border: 1px solid #dcdfe6;
}
</style>
