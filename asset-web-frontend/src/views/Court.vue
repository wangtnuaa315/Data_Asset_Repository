<template>
  <div class="court-page">
    <!-- 左右分栏主体 -->
    <div class="court-main-layout">
      
      <!-- 左侧：案件列表区域 -->
      <div class="left-panel">
        <!-- 搜索栏 -->
        <div class="search-bar">
          <el-select
            v-model="searchForm.region"
            placeholder="全部区域"
            clearable
            class="region-select"
            @change="handleSearchClick"
          >
            <el-option 
              v-for="region in regionList" 
              :key="region" 
              :label="region" 
              :value="region" 
            />
          </el-select>
          <el-input 
            v-model="searchForm.ah" 
            placeholder="搜索案号..." 
            clearable
            class="search-input"
            @keyup.enter="handleSearchClick"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" :icon="Search" @click="handleSearchClick" :loading="loading" class="search-btn">
            搜索
          </el-button>
        </div>

        <!-- 案件列表 -->
        <div class="case-list" v-loading="loading">
          <div v-if="caseList.length === 0 && !loading" class="empty-state">
            <el-empty description="点击搜索查看案件" :image-size="80" />
          </div>
          
          <div v-for="caseItem in caseList" :key="caseItem.case_code" 
               class="case-card"
               :class="{ active: currentCase?.case_code === caseItem.case_code }"
               @click="selectCase(caseItem)">
            <div class="case-card-header">
              <span class="case-number">{{ caseItem.ah || caseItem.case_code }}</span>
              <span class="dossier-count">卷宗数: {{ caseItem.dossier_count || 0 }}</span>
            </div>
            <div class="case-card-tags">
              <span v-if="caseItem.fymc" class="case-tag region">{{ caseItem.fymc }}</span>
              <span v-if="caseItem.has_indictment" class="case-tag indictment">起诉状</span>
              <span v-if="caseItem.has_defense" class="case-tag defense">答辩状</span>
              <span v-if="caseItem.has_court_record" class="case-tag record">庭审笔录</span>
              <span v-if="caseItem.has_judgement" class="case-tag judgement">判决书</span>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-box" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            small
            @current-change="handleSearch"
          />
        </div>
      </div>

      <!-- 右侧：卷宗详情区域 -->
      <div class="right-panel">
        <template v-if="currentCase">
          <!-- 案件头部 -->
          <div class="detail-header">
            <div class="detail-title">
              <span class="case-ah">案号：{{ currentCase.ah || currentCase.case_code }}</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="downloadCaseDossiers(currentCase)"
                class="download-all-btn"
              >
                <el-icon><Download /></el-icon> 下载全部
              </el-button>
            </div>
          </div>

          <!-- 卷宗分类筛选 -->
          <div class="dossier-filter">
            <el-select
              v-model="selectedCategory"
              placeholder="筛选卷宗分类"
              clearable
              class="category-filter-select"
            >
              <el-option
                v-for="cat in dossierCategories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </div>

          <!-- 卷宗树形列表 -->
          <div class="dossier-tree" v-loading="loadingDossiers">
            <template v-if="filteredDossierTree.length > 0">
              <div v-for="node in filteredDossierTree" :key="node.dossier_code" class="tree-node">
                <!-- 文件夹节点 -->
                <div v-if="node.is_folder" class="tree-folder">
                  <div class="tree-folder-header">
                    <span class="tree-icon folder">📁</span>
                    <span class="tree-folder-name">{{ node.name }}</span>
                    <span class="tree-folder-count">{{ getFilteredChildren(node).length }} 个文件</span>
                  </div>
                  <div class="tree-folder-children">
                    <div 
                      v-for="child in getFilteredChildren(node)" 
                      :key="child.dossier_code"
                      class="tree-file-item"
                    >
                      <span class="tree-icon file">📄</span>
                      <el-tooltip :content="child.name" placement="top" :show-after="500">
                        <span class="tree-file-name">{{ child.name }}</span>
                      </el-tooltip>
                      <span v-if="child.category_name" :class="['tree-category', getCategoryClass(child.category_name)]">
                        {{ child.category_name }}
                      </span>
                      <div class="tree-file-actions">
                        <el-button type="primary" link size="small" @click="previewDossier(child)">
                          <el-icon><View /></el-icon>
                        </el-button>
                        <el-button type="success" link size="small" @click="downloadDossier(child)">
                          <el-icon><Download /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 文件节点 -->
                <div v-else class="tree-file-item">
                  <span class="tree-icon file">📄</span>
                  <el-tooltip :content="node.name" placement="top" :show-after="500">
                    <span class="tree-file-name">{{ node.name }}</span>
                  </el-tooltip>
                  <span v-if="node.category_name" :class="['tree-category', getCategoryClass(node.category_name)]">
                    {{ node.category_name }}
                  </span>
                  <div class="tree-file-actions">
                    <el-button type="primary" link size="small" @click="previewDossier(node)">
                      <el-icon><View /></el-icon>
                    </el-button>
                    <el-button type="success" link size="small" @click="downloadDossier(node)">
                      <el-icon><Download /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无卷宗" :image-size="80" />
          </div>
        </template>
        
        <template v-else>
          <div class="no-selection">
            <el-empty description="请从左侧选择案件查看卷宗" :image-size="120" />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, View } from '@element-plus/icons-vue'
import { searchCases, getCaseDossiers, getDossierPreviewUrl, getDossierDownloadUrl, getCaseZipDownloadUrl, getDossierCategories, getRegions } from '../api/court'

// 搜索表单
const searchForm = reactive({
  ah: '',
  region: ''
})

// 卷宗分类列表
const dossierCategories = ref([])

// 区域列表（动态加载）
const regionList = ref([])

// 状态
const loading = ref(false)
const loadingDossiers = ref(false)

// 数据
const caseList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 选中的案件
const currentCase = ref(null)
const dossierTree = ref([])
const selectedCategory = ref(null)

// 分类名称映射到ID
const categoryNameToId = {
  '起诉状': 1, '答辩状': 2, '证据': 3, '其他文件': 4,
  '原审判决书': 5, '庭审笔录': 6, '诉讼请求变更申请': 7,
  '反诉状': 8, '量刑建议书': 9, '行政复议决定书': 10,
  '立案审批表': 11, '调解笔录': 12, '调解协议': 13,
  '送达回证': 14, '上诉状': 15, '听证笔录': 16, '谈话笔录': 17
}

// 初始化
onMounted(async () => {
  try {
    // 并行加载分类和区域列表
    const [categories, regions] = await Promise.all([
      getDossierCategories(),
      getRegions()
    ])
    dossierCategories.value = categories
    regionList.value = regions
  } catch (e) {
    console.error('加载初始化数据失败:', e)
  }
})

// 过滤后的卷宗树
const filteredDossierTree = computed(() => {
  if (!selectedCategory.value) return dossierTree.value
  
  return dossierTree.value.filter(node => {
    if (node.is_folder) {
      const hasMatch = node.children?.some(child => 
        categoryNameToId[child.category_name] === selectedCategory.value
      )
      return hasMatch
    } else {
      return categoryNameToId[node.category_name] === selectedCategory.value
    }
  })
})

// 获取过滤后的子节点
const getFilteredChildren = (node) => {
  if (!selectedCategory.value) return node.children || []
  return (node.children || []).filter(child => 
    categoryNameToId[child.category_name] === selectedCategory.value
  )
}

// 搜索（重置页码）
const handleSearchClick = () => {
  currentPage.value = 1
  handleSearch()
}

// 搜索
const handleSearch = async () => {
  loading.value = true
  
  try {
    const result = await searchCases({
      ah: searchForm.ah,
      region: searchForm.region,
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    caseList.value = result.items
    total.value = result.total
    
    // 如果有结果，自动选中第一个
    if (result.items.length > 0 && !currentCase.value) {
      selectCase(result.items[0])
    }
  } catch (error) {
    ElMessage.error('检索失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 选择案件
const selectCase = async (caseItem) => {
  currentCase.value = caseItem
  loadingDossiers.value = true
  selectedCategory.value = null
  
  try {
    const result = await getCaseDossiers(caseItem.case_code)
    dossierTree.value = result.tree || []
  } catch (error) {
    ElMessage.error('获取卷宗列表失败')
    dossierTree.value = []
  } finally {
    loadingDossiers.value = false
  }
}

// 预览卷宗
const previewDossier = (node) => {
  if (node.dossier_code) {
    window.open(getDossierPreviewUrl(node.dossier_code), '_blank')
  }
}

// 下载卷宗
const downloadDossier = (node) => {
  if (node.dossier_code) {
    window.open(getDossierDownloadUrl(node.dossier_code), '_blank')
  }
}

// 下载案件全部卷宗
const downloadCaseDossiers = (caseItem) => {
  if (!caseItem.case_code) return
  ElMessage.info('正在打包下载，请稍候...')
  window.open(getCaseZipDownloadUrl(caseItem.case_code), '_blank')
}

// 分类样式映射
const getCategoryClass = (categoryName) => {
  const classMap = {
    '起诉状': 'cat-indictment',
    '答辩状': 'cat-defense',
    '证据': 'cat-evidence',
    '庭审笔录': 'cat-record',
    '判决书': 'cat-judgement',
    '反诉状': 'cat-counterclaim',
    '立案审批表': 'cat-filing',
    '送达回证': 'cat-delivery',
    '上诉状': 'cat-appeal',
  }
  return classMap[categoryName] || 'cat-other'
}
</script>

<style scoped>
/* =====================================================
   Glassmorphism - Court Page 左右分栏布局
   ===================================================== */

.court-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.court-main-layout {
  display: flex;
  gap: 20px;
  height: 100%;
  overflow: hidden;
}

/* =====================================================
   左侧面板 - 案件列表
   ===================================================== */
.left-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  overflow: hidden;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.region-select {
  width: 120px !important;
}

.search-input {
  flex: 1;
}

.search-btn {
  height: 42px !important;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  padding: 0 16px !important;
}

.search-bar :deep(.el-input__wrapper),
.search-bar :deep(.el-select__wrapper) {
  height: 42px !important;
  border-radius: 10px !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  background: rgba(255, 255, 255, 0.08) !important;
  box-shadow: none !important;
}

.search-bar :deep(.el-input__wrapper:hover),
.search-bar :deep(.el-select__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.25) !important;
}

.search-bar :deep(.el-input__wrapper.is-focus),
.search-bar :deep(.el-select__wrapper.is-focus) {
  border-color: rgba(102, 126, 234, 0.5) !important;
}

.search-bar :deep(.el-input__inner) {
  color: #fff !important;
}

.search-bar :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

.search-bar :deep(.el-select__placeholder) {
  color: rgba(255, 255, 255, 0.7) !important;
}

/* 案件列表 */
.case-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.case-card {
  padding: 14px 16px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.case-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}

.case-card.active {
  background: rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.4);
}

.case-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.case-number {
  font-weight: 600;
  color: #fff;
  font-size: 14px;
}

.dossier-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(102, 126, 234, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

.case-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.case-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.case-tag.region {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.case-tag.indictment {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.case-tag.defense {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.case-tag.record {
  background: rgba(102, 126, 234, 0.2);
  color: #a5b4fc;
}

.case-tag.judgement {
  background: rgba(52, 199, 89, 0.2);
  color: #6ee7b7;
}

/* 分页 */
.pagination-box {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: center;
}

.pagination-box :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: rgba(255, 255, 255, 0.7);
  --el-pagination-button-disabled-color: rgba(255, 255, 255, 0.3);
}

.pagination-box :deep(.el-pager li) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.7) !important;
}

.pagination-box :deep(.el-pager li.is-active) {
  background: rgba(102, 126, 234, 0.3) !important;
  color: #fff !important;
}

/* =====================================================
   右侧面板 - 卷宗详情
   ===================================================== */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  overflow: hidden;
}

.no-selection {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 详情头部 */
.detail-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.case-ah {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.download-all-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  border-radius: 10px !important;
}

/* 分类筛选 */
.dossier-filter {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.category-filter-select {
  width: 200px !important;
}

.dossier-filter :deep(.el-select__wrapper) {
  height: 38px !important;
  border-radius: 10px !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  background: rgba(255, 255, 255, 0.08) !important;
  box-shadow: none !important;
}

.dossier-filter :deep(.el-select__placeholder) {
  color: rgba(255, 255, 255, 0.6) !important;
}

/* 卷宗树 */
.dossier-tree {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.tree-folder {
  margin-bottom: 16px;
}

.tree-folder-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  margin-bottom: 8px;
}

.tree-icon.folder {
  font-size: 18px;
}

.tree-folder-name {
  font-weight: 600;
  color: #fff;
  flex: 1;
}

.tree-folder-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.tree-folder-children {
  padding-left: 24px;
}

.tree-file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  transition: background 0.15s ease;
}

.tree-file-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.tree-icon.file {
  font-size: 16px;
}

.tree-file-name {
  flex: 1;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-category {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.tree-category.cat-indictment { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.tree-category.cat-defense { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.tree-category.cat-evidence { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.tree-category.cat-record { background: rgba(102, 126, 234, 0.2); color: #a5b4fc; }
.tree-category.cat-judgement { background: rgba(52, 199, 89, 0.2); color: #6ee7b7; }
.tree-category.cat-counterclaim { background: rgba(168, 85, 247, 0.2); color: #c4b5fd; }
.tree-category.cat-filing { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
.tree-category.cat-delivery { background: rgba(244, 114, 182, 0.2); color: #f472b6; }
.tree-category.cat-appeal { background: rgba(249, 115, 22, 0.2); color: #fb923c; }
.tree-category.cat-other { background: rgba(156, 163, 175, 0.2); color: #9ca3af; }

.tree-file-actions {
  display: flex;
  gap: 4px;
}

.tree-file-actions :deep(.el-button) {
  padding: 4px 8px !important;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

/* =====================================================
   滚动条样式
   ===================================================== */
.case-list::-webkit-scrollbar,
.dossier-tree::-webkit-scrollbar {
  width: 6px;
}

.case-list::-webkit-scrollbar-track,
.dossier-tree::-webkit-scrollbar-track {
  background: transparent;
}

.case-list::-webkit-scrollbar-thumb,
.dossier-tree::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.case-list::-webkit-scrollbar-thumb:hover,
.dossier-tree::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}
</style>
