<template>
  <div class="admin-system">
    <div class="page-header">
      <h2>系统设置</h2>
      <p>文件管理、脚本执行、系统配置</p>
    </div>

    <div class="system-grid">
      <!-- 文件管理 -->
      <div class="panel">
        <div class="panel-header">
          <h3><el-icon><Folder /></el-icon> 文件管理</h3>
          <div class="actions">
            <el-upload
              :show-file-list="false"
              :before-upload="handleUpload"
              :multiple="true"
              accept=".jpg,.jpeg,.png,.zip,.csv,.xlsx"
            >
              <el-button type="primary" :icon="Upload" size="small">上传</el-button>
            </el-upload>
            <el-button :icon="Refresh" size="small" @click="loadFiles">刷新</el-button>
          </div>
        </div>

        <div class="file-list" v-loading="filesLoading">
          <div
            v-for="file in files"
            :key="file.path"
            class="file-item"
            :class="{ 'is-dir': file.is_dir }"
          >
            <el-icon class="file-icon">
              <Folder v-if="file.is_dir" />
              <Picture v-else-if="isImage(file.name)" />
              <Document v-else />
            </el-icon>
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size" v-if="!file.is_dir">{{ formatSize(file.size) }}</span>
            <el-button
              type="danger"
              :icon="Delete"
              size="small"
              circle
              @click="handleDelete(file)"
            />
          </div>
          <el-empty v-if="files.length === 0" description="暂无文件" />
        </div>
      </div>

      <!-- 脚本执行 -->
      <div class="panel">
        <div class="panel-header">
          <h3><el-icon><VideoPlay /></el-icon> 脚本执行</h3>
        </div>

        <div class="script-list">
          <div
            v-for="script in scripts"
            :key="script.id"
            class="script-item"
          >
            <div class="script-info">
              <div class="script-name">{{ script.name }}</div>
              <div class="script-desc">{{ script.description }}</div>
            </div>
            <el-button
              type="primary"
              :icon="CaretRight"
              :loading="runningScript === script.id"
              @click="runScript(script.id)"
            >
              执行
            </el-button>
          </div>
        </div>

        <!-- 执行日志 -->
        <div class="log-section">
          <h4><el-icon><Document /></el-icon> 执行日志</h4>
          <div class="log-content" ref="logRef">
            <pre>{{ logOutput || '暂无日志' }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Folder, Upload, Refresh, Delete,
  Picture, Document, VideoPlay, CaretRight
} from '@element-plus/icons-vue'
import adminApi from '../../api/admin'

const logRef = ref(null)

// 文件管理
const files = ref([])
const filesLoading = ref(false)

// 脚本执行
const scripts = ref([
  { id: 'parse', name: '1. 解析元数据', description: '解析CSV/Excel，匹配图片' },
  { id: 'verify', name: '2. 文件分类', description: '按告警类型归档' },
  { id: 'register', name: '3. 资产注册', description: '注册到资产目录' },
  { id: 'import', name: '4. 数据导入', description: '导入业务数据' }
])
const runningScript = ref(null)
const logOutput = ref('')

// 加载文件列表
const loadFiles = async () => {
  filesLoading.value = true
  try {
    const res = await adminApi.listFiles()
    files.value = res.files
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    filesLoading.value = false
  }
}

// 上传文件
const handleUpload = async (file) => {
  try {
    await adminApi.uploadFile(file)
    ElMessage.success(`上传成功: ${file.name}`)
    loadFiles()
  } catch (error) {
    ElMessage.error('上传失败')
  }
  return false
}

// 删除文件
const handleDelete = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定删除 "${file.name}"？`,
      '确认删除',
      { type: 'warning' }
    )
    await adminApi.deleteFile(file.path)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 执行脚本
const runScript = async (scriptId) => {
  runningScript.value = scriptId
  logOutput.value += `\n[${new Date().toLocaleTimeString()}] 开始执行: ${scriptId}\n`

  try {
    const res = await adminApi.runScript(scriptId)
    
    if (res.success) {
      logOutput.value += res.output + '\n✅ 执行成功\n'
      ElMessage.success('执行成功')
    } else {
      logOutput.value += res.error + '\n❌ 执行失败\n'
      ElMessage.error('执行失败')
    }
  } catch (error) {
    logOutput.value += `\n❌ 错误: ${error.message}\n`
    ElMessage.error('执行出错')
  } finally {
    runningScript.value = null
    await nextTick()
    if (logRef.value) {
      logRef.value.scrollTop = logRef.value.scrollHeight
    }
  }
}

// 工具函数
const isImage = (name) => /\.(jpg|jpeg|png|gif)$/i.test(name)

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
/* Bento Grids / Apple Style - Admin System */

.admin-system {
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

.system-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.panel {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions :deep(.el-button) {
  border-radius: 10px;
}

/* 文件列表 */
.file-list {
  max-height: 350px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  transition: background 0.2s;
}

.file-item:hover {
  background: rgba(0, 122, 255, 0.05);
}

.file-icon {
  color: #86868B;
  font-size: 20px;
}

.file-item.is-dir .file-icon {
  color: #007AFF;
}

.file-name {
  flex: 1;
  color: #1D1D1F;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #AEAEB2;
  font-size: 12px;
}

/* 脚本列表 */
.script-list {
  margin-bottom: 24px;
}

.script-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #F5F5F7;
  border-radius: 12px;
  margin-bottom: 12px;
}

.script-name {
  font-size: 14px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.script-desc {
  font-size: 12px;
  color: #86868B;
}

.script-item :deep(.el-button) {
  border-radius: 10px;
}

/* 日志区域 */
.log-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px 0;
}

.log-content {
  background: #1D1D1F;
  border-radius: 12px;
  padding: 16px;
  max-height: 180px;
  overflow-y: auto;
}

.log-content pre {
  color: #86868B;
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
