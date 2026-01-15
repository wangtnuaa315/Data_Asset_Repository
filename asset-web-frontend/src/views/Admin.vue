<template>
  <div class="admin-container">
    <div class="admin-body">
      <!-- 页面标题 + 返回按钮 -->
      <div class="page-header">
        <el-button class="back-btn" @click="goBack" circle>
          <el-icon><Back /></el-icon>
        </el-button>
        <div class="page-title">
          <el-icon :size="28"><Guide /></el-icon>
          <h1>管理员操作指南</h1>
        </div>
      </div>

      <!-- 文件上传提示 -->
      <div class="panel">
        <div class="panel-title">
          <el-icon :size="24"><Folder /></el-icon>
          文件管理
        </div>

        <div class="notice-card blue">
          <div class="notice-header">
            <div class="notice-icon blue">
              <el-icon :size="28"><Upload /></el-icon>
            </div>
            <div class="notice-info">
              <div class="notice-title">使用 FileBrowser 上传文件</div>
              <div class="notice-subtitle">推荐使用专业文件管理工具，支持大文件、断点续传</div>
            </div>
          </div>
          <div class="notice-content">
            请访问 NAS 文件管理系统上传告警图片和 CSV 数据文件。<br>
            上传目录：<strong>00_Work_Area / new_uploads</strong>
          </div>
          <a :href="fileBrowserUrl" target="_blank" class="notice-link">
            <el-icon><Link /></el-icon>
            打开 FileBrowser
          </a>
        </div>
      </div>

      <!-- 脚本执行提示 -->
      <div class="panel">
        <div class="panel-title">
          <el-icon :size="24"><Monitor /></el-icon>
          数据处理脚本
          <el-tag type="warning" size="small">以"应急安全"模块为例</el-tag>
        </div>

        <div class="notice-card orange">
          <div class="notice-header">
            <div class="notice-icon orange">
              <el-icon :size="28"><Monitor /></el-icon>
            </div>
            <div class="notice-info">
              <div class="notice-title">在服务器上执行脚本</div>
              <div class="notice-subtitle">通过 SSH 连接服务器执行以下命令</div>
            </div>
          </div>
          <div class="notice-content">
            <el-alert 
              title="以下命令以「应急安全」业务模块为例，其他业务模块请参考对应目录下的脚本" 
              type="warning" 
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            />
            文件上传完成后，按顺序执行以下脚本处理数据：
          </div>

          <div class="code-block">
            <pre><span class="comment"># 1. SSH 连接服务器</span>
<span class="command">ssh</span> root@192.168.2.170

<span class="comment"># 2. 进入项目目录</span>
<span class="command">cd</span> <span class="path">/opt/data_asset</span>

<span class="comment"># 3. 执行数据处理脚本（按顺序）</span>
<span class="command">python3</span> scripts/emergency/parse_metadata.py    <span class="comment"># 解析元数据</span>
<span class="command">python3</span> scripts/emergency/verify_structure.py  <span class="comment"># 验证文件结构</span>
<span class="command">python3</span> scripts/common/register_assets.py      <span class="comment"># 注册资产</span>
<span class="command">python3</span> scripts/emergency/import_from_csv.py   <span class="comment"># 导入业务数据</span></pre>
          </div>
        </div>

        <!-- 步骤说明 -->
        <div class="step-list">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>解析元数据</h4>
              <p>解压 ZIP 包，读取 CSV 文件，匹配图片与告警记录</p>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>验证文件结构</h4>
              <p>检查图片完整性，按告警类型分类归档</p>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>注册资产</h4>
              <p>将图片注册到资产目录表 <code>asset_catalog</code></p>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>导入业务数据</h4>
              <p>将告警信息导入 <code>emergency_alarm_assets</code> 表</p>
            </div>
          </div>
          <!-- 最后一步 - 检索提醒 -->
          <div class="step-item highlight">
            <div class="step-number success">
              <el-icon><Check /></el-icon>
            </div>
            <div class="step-content">
              <h4>🎉 数据导入完成！现在可以检索了</h4>
              <p>导入成功后，返回检索页面查看新数据</p>
              <el-button type="primary" size="small" @click="goBack" class="search-btn">
                <el-icon><Search /></el-icon>
                前往检索
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Guide, Folder, Upload, Link, Monitor, Back, Check, Search
} from '@element-plus/icons-vue'

const router = useRouter()

// FileBrowser URL - 可通过环境变量配置
const fileBrowserUrl = import.meta.env.VITE_FILEBROWSER_URL || 'http://192.168.2.170:8081/'

const goBack = () => {
  router.push('/emergency')
}
</script>

<style scoped>
/* =====================================================
   Bento Grids / Apple Style - Admin Guide
   ===================================================== */

.admin-container {
  min-height: 100vh;
  background: transparent;
  position: relative;
  z-index: 1;
}

/* 页面标题 + 返回按钮 */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  background: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  color: #86868B;
}

.back-btn:hover {
  background: #007AFF !important;
  color: white;
  transform: translateX(-2px);
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title .el-icon {
  color: #007AFF;
}

.page-title h1 {
  font-size: 24px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, sans-serif;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

/* 主体区域 */
.admin-body {
  max-width: 1000px;
  margin: 32px auto;
  padding: 0 32px;
}

/* 卡片 */
.panel {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1D1D1F;
  font-family: 'Inter', -apple-system, sans-serif;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 提醒卡片 */
.notice-card {
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}

.notice-card.blue {
  background: linear-gradient(135deg, #E8F4FD 0%, #F0E6FA 100%);
  border: 1px solid rgba(0, 122, 255, 0.2);
}

.notice-card.orange {
  background: linear-gradient(135deg, #FFF8E6 0%, #FFF0D4 100%);
  border: 1px solid rgba(255, 149, 0, 0.3);
}

.notice-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.notice-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notice-icon.blue {
  background: rgba(0, 122, 255, 0.15);
  color: #007AFF;
}

.notice-icon.orange {
  background: rgba(255, 149, 0, 0.15);
  color: #FF9500;
}

.notice-info {
  flex: 1;
}

.notice-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  font-family: 'Inter', -apple-system, sans-serif;
  margin-bottom: 4px;
}

.notice-subtitle {
  font-size: 13px;
  color: #86868B;
}

.notice-content {
  color: #424245;
  font-size: 14px;
  line-height: 1.7;
}

.notice-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 24px;
  background: #007AFF;
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.notice-link:hover {
  background: #0066CC;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

/* 命令行样式 */
.code-block {
  background: #1D1D1F;
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
  overflow-x: auto;
}

.code-block pre {
  color: #E5E5E7;
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  margin: 0;
  line-height: 1.8;
}

.code-block .comment {
  color: #6B7280;
}

.code-block .command {
  color: #5AC8FA;
}

.code-block .path {
  color: #34C759;
}

/* 步骤列表 */
.step-list {
  margin-top: 8px;
}

.step-item {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #E8E8ED;
}

.step-item:last-child {
  border-bottom: none;
}

.step-number {
  width: 32px;
  height: 32px;
  background: #007AFF;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-number.success {
  background: #34C759;
}

.step-content h4 {
  font-size: 15px;
  font-weight: 600;
  color: #1D1D1F;
  font-family: 'Inter', -apple-system, sans-serif;
  margin: 0 0 4px 0;
}

.step-content p {
  font-size: 13px;
  color: #86868B;
  margin: 0;
}

.step-content code {
  background: #F5F5F7;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: #007AFF;
}

/* 最后一步高亮 */
.step-item.highlight {
  background: linear-gradient(135deg, #E8F4FD 0%, #E6FAF0 100%);
  margin: 16px -28px 0 -28px;
  padding: 20px 28px;
  border-radius: 0 0 20px 20px;
  border-bottom: none;
}

.search-btn {
  margin-top: 12px;
  border-radius: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .admin-body {
    padding: 0 16px;
    margin: 16px auto;
  }
  
  .notice-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
