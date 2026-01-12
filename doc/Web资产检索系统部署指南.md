# Web资产检索系统部署指�?

## 📋 系统信息

**访问地址**�?
- 前端界面：http://192.168.2.170:8082
- 后端API文档：http://192.168.2.170:8003/docs
- FileBrowser：http://192.168.2.170:8081（管理员工具�?

**技术栈**�?
- 后端：FastAPI + asyncpg + Pydantic
- 前端：Vue 3 + Element Plus + Vite
- 数据库：PostgreSQL 15
- 部署：Docker Compose

---

## �?代码上传到服务器

### 准备工作

**本地代码目录**�?
```
c:\Users\wangt\Desktop\语义检索增强部署\192.168.2.170�?92.168.1.77）\
├── asset-web-backend/      # 后端代码
├── asset-web-frontend/     # 前端代码
├── docker-compose.yml      # 更新后的编排文件
└── Dockerfile.filebrowser  # FileBrowser镜像文件
```

**服务器目标目�?*：`/opt/data_asset/`

### 方法一：使用SFTP上传（推荐）

**步骤1：连接服务器**

```bash
# Windows PowerShell或命令提示符
sftp root@192.168.2.170
```

**步骤2：切换到目标目录**

```bash
cd /opt/data_asset
```

**步骤3：上传后端代�?*

```bash
# 创建后端目录（如果不存在�?
mkdir asset-web-backend

# 上传后端代码（在SFTP会话中）
put -r "C:\Users\wangt\Desktop\语义检索增强部署\192.168.2.170�?92.168.1.77）\asset-web-backend\*" asset-web-backend/
```

**步骤4：上传前端代�?*

```bash
# 创建前端目录
mkdir asset-web-frontend

# 上传前端代码
put -r "C:\Users\wangt\Desktop\语义检索增强部署\192.168.2.170�?92.168.1.77）\asset-web-frontend\*" asset-web-frontend/
```

**步骤5：更新配置文�?*

```bash
# 上传更新的docker-compose.yml
put "C:\Users\wangt\Desktop\语义检索增强部署\192.168.2.170�?92.168.1.77）\docker-compose.yml" docker-compose.yml
```

### 方法二：使用SCP命令（Linux/Mac�?

如果使用Linux或Mac，可以用SCP命令一次性上传：

```bash
# 上传后端
scp -r "/path/to/asset-web-backend" root@192.168.2.170:/opt/data_asset/

# 上传前端
scp -r "/path/to/asset-web-frontend" root@192.168.2.170:/opt/data_asset/

# 更新docker-compose.yml
scp "/path/to/docker-compose.yml" root@192.168.2.170:/opt/data_asset/
```

### 方法三：使用WinSCP（Windows图形界面�?

1. 下载并安装WinSCP
2. 连接�?`192.168.2.170`（用户名：root�?
3. 左侧（本地）：导航到本地代码目录
4. 右侧（服务器）：导航�?`/opt/data_asset/`
5. 将以下目�?文件拖拽上传�?
   - `asset-web-backend/` 整个文件�?
   - `asset-web-frontend/` 整个文件�?
   - `docker-compose.yml` 文件

### 验证上传完成

上传完成后，在服务器上验证：

```bash
cd /opt/data_asset

# 检查目录结�?
ls -la

# 应该看到�?
# asset-web-backend/
# asset-web-frontend/
# docker-compose.yml
# scripts/
# config.yaml
# ...

# 检查后端文�?
ls -la asset-web-backend/
# 应该看到：app/, Dockerfile, requirements.txt, README.md

# 检查前端文�?
ls -la asset-web-frontend/
# 应该看到：src/, package.json, vite.config.js, Dockerfile, nginx.conf
```

---

## �🚀 快速部�?

### 步骤1：停止现有容�?

```bash
cd /opt/data_asset
docker-compose down
```

### 步骤2：构建并启动新服�?

```bash
docker-compose up -d --build
```

### 步骤3：查看容器状�?

```bash
docker ps
```

应该看到5个运行中的容器：
- `asset_catalog_db` - PostgreSQL数据�?
- `asset_catalog_pgadmin` - PgAdmin管理界面
- `asset_file_manager` - FileBrowser文件管理�?
- `asset_web_api` - 资产检索后端API
- `asset_web_ui` - 资产检索前端界�?

### 步骤4：查看日�?

```bash
# 查看后端日志
docker logs asset_web_api --tail 50

# 查看前端日志
docker logs asset_web_ui --tail 50
```

### 步骤5：访问系�?

打开浏览器访问：http://192.168.2.170:8082

---

## �?数据准备与导入流�?

### 完整数据流程�?

```
告警图片 + metadata_emergency.csv
    �?(上传到new_uploads)
/data/nas_data/00_Work_Area/new_uploads/
    �?(执行verify_structure.py)
/data/nas_data/10_Official_Library/02_应急_安全/02_历史告警归档/
    �?(执行register_assets.py)
PostgreSQL asset_catalog�?
    �?(执行import_from_csv.py)
PostgreSQL emergency_alarm_assets�?
    �?(Web查询)
http://192.168.2.170:8082 界面展示
```

### 步骤1：准备数据文�?

需要准备两类文件：

**1. 告警图片文件**
- 格式：`.jpg`, `.png`, `.jpeg`
- 命名：任意名称（如`alarm_001.jpg`, `fire_detection.png`�?
- 数量：无限制

**2. metadata_emergency.csv文件**

CSV格式，必须包含以下列�?

```csv
filename,alarm_name,analysis_result,alarm_time,device_code,category
alarm_001.jpg,火点检测报警事�?检测到疑似火情,2025-10-15 14:30:00,DEV001,历史告警归档
alarm_002.png,烟雾检测报警事�?检测到烟雾,2025-10-16 09:15:00,DEV002,历史告警归档
```

**字段说明**�?
- `filename`: 图片文件名（必须与实际文件名完全一致）
- `alarm_name`: 告警类型名称
- `analysis_result`: AI分析结果（可选）
- `alarm_time`: 告警时间（格式：YYYY-MM-DD HH:MM:SS�?
- `device_code`: 设备编码（可选）
- `category`: 分类目录（默认：历史告警归档�?

> **多重告警**：如果同一图片触发多个告警，在CSV中添加多行，使用相同的filename即可�?

### 步骤2：上传文件到服务�?

**上传目录**：`/data/nas_data/00_Work_Area/new_uploads/`

**方法一：使用SFTP**

```bash
# 从Windows客户端上�?
sftp root@192.168.2.170
cd /data/nas_data/00_Work_Area/new_uploads
put *.jpg
put metadata_emergency.csv
```

**方法二：使用FileBrowser**

1. 访问：http://192.168.2.170:8081
2. 登录（用户名：admin，密码：自动生成的密码）
3. 导航到：`00_Work_Area/new_uploads/`
4. 上传图片文件和`metadata_emergency.csv`

**方法三：直接复制到服务器**

```bash
# 在服务器�?
cp /path/to/your/files/*.jpg /data/nas_data/00_Work_Area/new_uploads/
cp /path/to/your/metadata_emergency.csv /data/nas_data/00_Work_Area/new_uploads/
```

### 步骤3：执行数据处理脚�?

**激活Python虚拟环境**

```bash
cd /opt/data_asset
source venv/bin/activate
```

**3.1 分类和移动文�?*

```bash
python scripts/emergency/verify_structure.py
```

**功能**�?
- 读取`metadata_emergency.csv`
- 根据告警类型和时间自动分类文�?
- 移动到规范目录（如`02_历史告警归档/火点检测报警事�?2025_Q4/`�?
- 处理多重告警（组合目录名�?

**输出示例**�?
```
�?成功处理 15 个文�?
📁 生成目录结构�?
   - 火点检测报警事�?2025_Q4/ (5个文�?
   - 烟雾检测报警事�?2025_Q4/ (7个文�?
   - 火点检测报警事�?烟雾检测报警事�?2025_Q4/ (3个文�?
```

**3.2 注册资产到数据库**

```bash
python scripts/common/register_assets.py
```

**功能**�?
- 扫描`10_Official_Library`目录
- 计算文件MD5哈希
- 注册到`asset_catalog`�?
- 自动去重

**输出示例**�?
```
📊 扫描结果�?
   - 新增资产�?5�?
   - 已存在（跳过）：0�?
   - 总资产数�?5�?
```

**3.3 导入业务数据**

```bash
python scripts/emergency/import_from_csv.py
```

**功能**�?
- 读取`new_uploads/metadata_emergency.csv`
- 匹配`asset_id`
- 导入到`emergency_alarm_assets`�?

**输出示例**�?
```
�?成功导入 18 条告警记�?
   - 关联�?15 个资产文�?
   - 多重告警�?个文�?
```

### 步骤4：验证数�?

**4.1 检查数据库**

```bash
# 连接数据�?
docker exec -it asset_catalog_db psql -U admin -d asset_catalog

# 查询资产总数
SELECT COUNT(*) FROM asset_catalog WHERE status = 'ready';

# 查询告警记录
SELECT COUNT(*) FROM emergency_alarm_assets;

# 查看最�?0条告�?
SELECT 
    a.filename,
    e.alarm_name,
    e.alarm_time
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
ORDER BY e.alarm_time DESC
LIMIT 10;
```

**4.2 检查文件结�?*

```bash
# 查看分类后的目录
ls -la /data/nas_data/10_Official_Library/02_应急_安全/02_历史告警归档/
```

### 步骤5：Web界面查询

1. 访问：http://192.168.2.170:8082
2. 选择告警类型（如"火点检测报警事�?�?
3. 设置时间范围
4. 点击"搜索"
5. 查看缩略图网�?
6. 点击图片查看详情

---

## 🔄 日常使用流程

### 添加新的告警数据

1. **准备新数�?*
   - 新图片放到`new_uploads/`
   - 更新`metadata_emergency.csv`（追加新行）

2. **执行处理**
   ```bash
   cd /opt/data_asset
   source venv/bin/activate
   python scripts/emergency/verify_structure.py
   python scripts/common/register_assets.py
   python scripts/emergency/import_from_csv.py
   ```

3. **刷新Web界面**
   - 新数据立即可搜索

### 批量导入历史数据

```bash
# 如果有大量历史数�?
cd /opt/data_asset
source venv/bin/activate

# 一次性处�?
python scripts/emergency/verify_structure.py && \
python scripts/common/register_assets.py && \
python scripts/emergency/import_from_csv.py
```

---

## ��?本地开发模式（可选）

如果需要本地开发调试：

### 后端开�?

```bash
cd asset-web-backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开�?

```bash
cd asset-web-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:8082

---

## 📊 功能说明

### 搜索功能

1. **告警类型筛�?*：下拉多选框
2. **设备编码**：模糊搜�?
3. **时间范围**：日期范围选择�?
4. **关键�?*：AI分析结果搜索

### 结果展示

- 缩略图网格（3-4列自适应�?
- 悬停显示操作按钮（预�?下载�?
- 多选批量下�?
- 分页展示�?0/50/100�?页）

### 详情查看

- 大图预览
- 完整元数据展�?
- 文件路径复制
- 单文件下�?

---

## 🎨 UI特�?

### 科技感深色主�?

- 深色背景：`#0a0e27` �?`#131729`
- 主色调：蓝紫渐变 `#00d4ff` �?`#7b2ff7`
- 光效动画：悬停光晕效�?
- 流畅过渡：所有交�?.3s动画

### 响应式设�?

- 网格自适应布局
- 移动端友�?
- 跨浏览器兼容

---

## 🐛 故障排查

### 问题1：前端无法访�?

```bash
# 检查容器状�?
docker ps | grep asset_web_ui

# 查看日志
docker logs asset_web_ui

# 重启容器
docker restart asset_web_ui
```

### 问题2：API请求失败

```bash
# 检查后端容�?
docker ps | grep asset_web_api

# 查看详细日志
docker logs asset_web_api --tail 100

# 检查数据库连接
docker exec asset_web_api ping db
```

### 问题3：缩略图无法加载

```bash
# 进入后端容器检�?
docker exec -it asset_web_api sh

# 检查缩略图目录
ls -la /tmp/thumbnails/

# 检查NAS挂载
ls -la /data/nas_data/
```

### 问题4：搜索无结果

```sql
-- 连接数据库检查数�?
docker exec -it asset_catalog_db psql -U admin -d asset_catalog

-- 查询资产总数
SELECT COUNT(*) FROM asset_catalog WHERE status = 'ready';

-- 查询告警记录
SELECT COUNT(*) FROM emergency_alarm_assets;
```

---

## 🔐 安全建议

1. **修改默认密码**
   - 数据库密码已设置，建议定期更�?
   - FileBrowser首次登录后修改密�?

2. **防火墙配�?*
   ```bash
   # 仅允许内网访�?
   ufw allow from 192.168.2.0/24 to any port 8082
   ```

3. **HTTPS配置**（生产环境）
   - 使用Nginx反向代理
   - 配置SSL证书

---

## 📈 性能优化

### 后端优化

- 数据库连接池�?-20个连�?
- 缩略图缓存：`/tmp/thumbnails/`
- 异步I/O：asyncpg驱动

### 前端优化

- Gzip压缩：Nginx自动启用
- 静态资源缓存：30�?
- 代码分割：Vite自动优化

---

## 🔄 更新升级

### 更新后端

```bash
cd asset-web-backend
# 修改代码�?
docker-compose build asset_web_backend
docker-compose up -d asset_web_backend
```

### 更新前端

```bash
cd asset-web-frontend
# 修改代码�?
docker-compose build asset_web_frontend
docker-compose up -d asset_web_frontend
```

---

## 📞 技术支�?

遇到问题请检查：
1. Docker日志：`docker logs <container_name>`
2. 数据库连接：确保PostgreSQL正常运行
3. NAS挂载：确保`/data/nas_data`可访�?
4. API文档：http://192.168.2.170:8000/docs

---

## �?验证清单

部署完成后验证以下项目：

- [ ] 前端界面可访�?(http://192.168.2.170:8082)
- [ ] 后端API文档可访�?(http://192.168.2.170:8000/docs)
- [ ] 搜索功能正常
- [ ] 缩略图正常加�?
- [ ] 文件下载功能正常
- [ ] 详情查看正常
- [ ] 批量下载功能正常
- [ ] 分页功能正常

