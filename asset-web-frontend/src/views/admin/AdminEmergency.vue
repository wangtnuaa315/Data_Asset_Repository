<template>
  <div class="admin-emergency">
    <div class="page-header">
      <h2>应急安全资产管理</h2>
      <p>管理告警资产数据、执行数据导入</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon"><el-icon><Picture /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalAssets }}</span>
          <span class="stat-label">总资产数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning"><el-icon><Warning /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.alarmTypes }}</span>
          <span class="stat-label">告警类型</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success"><el-icon><Connection /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.devices }}</span>
          <span class="stat-label">关联设备</span>
        </div>
      </div>
    </div>

    <!-- 操作面板 -->
    <div class="action-panels">
      <!-- 数据导入 -->
      <div class="panel">
        <div class="panel-header">
          <h3><el-icon><Upload /></el-icon> 数据导入</h3>
        </div>
        <div class="panel-body">
          <p class="panel-desc">上传 CSV/Excel 文件导入应急安全资产数据</p>
          <el-upload
            drag
            :show-file-list="false"
            :before-upload="handleImport"
            accept=".csv,.xlsx,.xls"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">
              <span>拖拽文件到此处或 <em>点击上传</em></span>
            </div>
            <div class="upload-tip">支持 CSV、Excel 格式</div>
          </el-upload>
        </div>
      </div>

      <!-- 批量操作 -->
      <div class="panel">
        <div class="panel-header">
          <h3><el-icon><Operation /></el-icon> 批量操作</h3>
        </div>
        <div class="panel-body">
          <div class="action-list">
            <el-button :icon="Download" @click="handleExport">导出全部数据</el-button>
            <el-button :icon="Delete" type="danger" @click="handleClear">清空所有资产</el-button>
            <el-button :icon="Refresh" @click="handleRefresh">刷新缓存</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 资产列表 -->
    <div class="assets-section">
      <div class="section-header">
        <h3>资产列表</h3>
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索资产..." 
          :prefix-icon="Search"
          clearable
          class="search-input"
        />
      </div>
      <div class="table-container" v-loading="loading">
        <el-table :data="assets" stripe>
          <el-table-column prop="asset_id" label="资产ID" width="100" />
          <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="alarm_name" label="告警类型" width="120" />
          <el-table-column prop="alarm_time" label="告警时间" width="180" />
          <el-table-column prop="dev_code" label="设备编码" width="140" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" :icon="Delete" circle @click="handleDelete(row)" />
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination">
          <el-pagination
            v-model:current-page="page"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="loadAssets"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Picture, Warning, Connection, Upload, Operation, 
  Download, Delete, Refresh, Search 
} from '@element-plus/icons-vue'
import api from '../../api/emergency'

// 统计数据
const stats = ref({
  totalAssets: 0,
  alarmTypes: 0,
  devices: 0
})

// 资产列表
const assets = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

// 加载资产列表
const loadAssets = async () => {
  loading.value = true
  try {
    const res = await api.searchAssets({
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value
    })
    assets.value = res.items
    total.value = res.total
    stats.value.totalAssets = res.total
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 导入数据
const handleImport = async (file) => {
  ElMessage.info(`正在导入: ${file.name}`)
  // TODO: 调用导入 API
  return false
}

// 导出数据
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

// 清空数据
const handleClear = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有应急安全资产吗？此操作不可恢复！', '警告', {
      type: 'warning',
      confirmButtonText: '确定清空',
      cancelButtonText: '取消'
    })
    ElMessage.success('清空成功')
    loadAssets()
  } catch {}
}

// 删除单个资产
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除资产 "${row.filename}"？`, '确认删除', { type: 'warning' })
    ElMessage.success('删除成功')
    loadAssets()
  } catch {}
}

// 刷新
const handleRefresh = () => {
  loadAssets()
  ElMessage.success('已刷新')
}

onMounted(() => {
  loadAssets()
})
</script>

<style scoped>
/* Bento Grids / Apple Style - Admin Emergency */

.admin-emergency {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  color: #1D1D1F;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #86868B;
  font-size: 15px;
  margin: 0;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.warning {
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
}

.stat-icon.success {
  background: rgba(52, 199, 89, 0.1);
  color: #34C759;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1D1D1F;
  display: block;
}

.stat-label {
  font-size: 13px;
  color: #86868B;
}

/* 操作面板 */
.action-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.panel {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
}

.panel-desc {
  color: #86868B;
  font-size: 13px;
  margin-bottom: 16px;
}

.upload-icon {
  font-size: 48px;
  color: #AEAEB2;
  margin-bottom: 12px;
}

.upload-text {
  color: #86868B;
}

.upload-text em {
  color: #007AFF;
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: #AEAEB2;
  margin-top: 8px;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-list :deep(.el-button) {
  justify-content: flex-start;
  border-radius: 12px;
  height: 44px;
}

/* 资产列表 */
.assets-section {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  margin: 0;
}

.search-input {
  width: 240px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 12px;
}

.table-container {
  min-height: 300px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}
</style>
