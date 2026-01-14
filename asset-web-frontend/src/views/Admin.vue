<template>
  <div class="admin-container">
    <div class="admin-header">
      <h1>
        <el-icon><Setting /></el-icon>
        管理中心
      </h1>
      <el-button @click="goBack" :icon="Back">返回检索</el-button>
    </div>

    <div class="admin-content">
      <!-- 左侧：文件管理 -->
      <div class="panel file-panel">
        <div class="panel-header">
          <h2><el-icon><Folder /></el-icon> 文件管理</h2>
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

      <!-- 右侧：脚本执行 -->
      <div class="panel script-panel">
        <div class="panel-header">
          <h2><el-icon><VideoPlay /></el-icon> 脚本执行</h2>
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
          <h3><el-icon><Document /></el-icon> 执行日志</h3>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting, Back, Folder, Upload, Refresh, Delete,
  Picture, Document, VideoPlay, CaretRight
} from '@element-plus/icons-vue'
import adminApi from '../api/admin'

const router = useRouter()
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
    if (error.response?.status === 403) {
      ElMessage.error('需要管理员权限')
      router.push('/login')
    } else {
      ElMessage.error('加载失败')
    }
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
  return false // 阻止默认上传
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
    // 滚动到底部
    await nextTick()
    if (logRef.value) {
      logRef.value.scrollTop = logRef.value.scrollHeight
    }
  }
}

// 返回检索页
const goBack = () => {
  router.push('/emergency')
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
.admin-container {
  padding: 20px;
  min-height: 100vh;
  background: var(--bg-primary);
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.admin-header h1 {
  color: var(--primary-color);
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h2 {
  color: var(--text-primary);
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.file-list {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
}

.file-item:hover {
  background: var(--bg-hover);
}

.file-icon {
  color: var(--text-secondary);
  font-size: 20px;
}

.file-item.is-dir .file-icon {
  color: var(--primary-color);
}

.file-name {
  flex: 1;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: var(--text-muted);
  font-size: 12px;
}

.script-list {
  margin-bottom: 20px;
}

.script-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 10px;
}

.script-name {
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 4px;
}

.script-desc {
  color: var(--text-muted);
  font-size: 12px;
}

.log-section h3 {
  color: var(--text-primary);
  font-size: 14px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.log-content {
  background: #0d1117;
  border-radius: 8px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.log-content pre {
  color: #8b949e;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
