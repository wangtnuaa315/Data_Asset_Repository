<template>
  <div class="emergency-page">
    <!-- 搜索区域 -->
    <!-- 搜索区域 -->
    <div class="search-section glass-effect">
      <div class="search-header">
        <div class="header-title glow-text">
          <el-icon :size="20"><Search /></el-icon>
          <span>智能检索</span>
        </div>
        <div class="header-decoration"></div>
      </div>

      <el-form :model="searchForm" label-position="top" class="search-form">
        <el-row :gutter="20">
          <!-- 告警类型 -->
          <el-col :xs="24" :sm="12" :md="6" :lg="6">
            <el-form-item label="告警类型">
              <el-select
                v-model="searchForm.alarm_types"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="全部类型"
                clearable
                class="tech-input"
              >
                <template #prefix><el-icon><Warning /></el-icon></template>
                <el-option
                  v-for="type in alarmTypes"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 时间范围 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="-"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                :shortcuts="dateShortcuts"
                class="tech-input date-range-full"
              />
            </el-form-item>
          </el-col>

          <!-- 设备和关键词 -->
          <el-col :xs="24" :sm="12" :md="5" :lg="5">
             <el-form-item label="设备编码">
               <el-input 
                 v-model="searchForm.dev_code" 
                 placeholder="设备ID" 
                 clearable
                 class="tech-input"
               >
                 <template #prefix><el-icon><Cpu /></el-icon></template>
               </el-input>
             </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="5" :lg="5">
              <el-form-item label="AI分析关键词">
                <el-input 
                  v-model="searchForm.keyword" 
                  placeholder="如: 火点, 烟雾..." 
                  clearable
                  class="tech-input"
                  @keyup.enter="handleSearch"
                >
                  <template #prefix><el-icon><Aim /></el-icon></template>
                </el-input>
              </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 搜索按钮栏 (浮动在右下或独立一行) -->
        <div class="search-actions">
           <el-button type="primary" :icon="Search" @click="handleSearch" :loading="loading" class="action-btn">
             立即检索
           </el-button>
           <el-button :icon="Refresh" @click="handleReset" class="reset-btn">
             重置条件
           </el-button>
        </div>
      </el-form>
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
              :preview-src-list="[row.thumbnail_url.replace('/thumbnail/', '/download/')]"
              fit="cover"
              class="table-thumbnail"
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
        <el-table-column prop="analysis" label="AI分析" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.analysis && row.analysis.trim()" type="success" effect="dark" size="small">
              {{ row.analysis }}
            </el-tag>
            <span v-else class="no-analysis">暂无</span>
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
  gap: 20px;
  overflow: auto;
}

.search-section {
  flex-shrink: 0;
  padding: 20px 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}

.search-section::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
  opacity: 0.5;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
  letter-spacing: 1px;
}

.search-form {
  position: relative;
}

/* 覆盖Element Form Item样式 */
:deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 12px;
  padding-bottom: 4px;
}

.tech-input {
  width: 100%;
}

.date-range-full {
  width: 100% !important;
}

.search-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.action-btn {
  padding: 0 30px;
  height: 40px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(26, 31, 58, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 16px;
  backdrop-filter: blur(5px);
}

.stats, .selected-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
}

.stats strong, .selected-info strong {
  color: var(--primary-color);
  font-size: 18px;
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--primary-color);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  flex: 1;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

/* 列表视图容器 */
.results-list {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
}

/* 表格深色主题适配 */
:deep(.asset-table) {
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  --el-table-header-bg-color: rgba(0, 0, 0, 0.3);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-text-color: var(--text-regular);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-row-hover-bg-color: rgba(0, 212, 255, 0.08);
  background-color: transparent !important;
}

:deep(.el-table__inner-wrapper::before) {
  background-color: rgba(255, 255, 255, 0.05);
}

:deep(.el-table td.el-table__cell),
:deep(.el-table th.el-table__cell) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  background-color: transparent !important;
}

:deep(.el-table__body-wrapper) {
  background-color: transparent !important;
}

:deep(.el-table__header-wrapper) {
  background-color: transparent !important;
}

/* 表格缩略图 */
.table-thumbnail {
  width: 80px;
  height: 50px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 暂无分析样式 */
.no-analysis {
  color: #6b7280;
  font-style: italic;
  font-size: 12px;
}

/* 分页组件深色主题适配 */
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: transparent;
  --el-pagination-button-disabled-bg-color: transparent;
  --el-pagination-hover-color: var(--primary-color);
}

:deep(.el-pagination .el-select .el-input .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

:deep(.el-pagination .el-pager li) {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin: 0 2px;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--primary-color) !important;
  color: white !important;
  border-color: var(--primary-color);
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background: transparent !important;
  color: var(--text-secondary) !important;
}

:deep(.el-pagination .el-pagination__jump) {
  color: var(--text-secondary);
}

:deep(.el-pagination .el-pagination__jump .el-input .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

:deep(.el-pagination .el-pagination__total) {
  color: var(--text-secondary);
}
</style>
