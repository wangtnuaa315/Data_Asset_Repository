# 资产检索系统后端API

基于FastAPI的资产检索系统后端服务。

## 功能特性

- 应急安全告警资产搜索
- 图片缩略图生成
- 文件下载
- 自动API文档

## 本地开发

1. 安装依赖：
```bash
cd asset-web-backend
pip install -r requirements.txt
```

2. 启动开发服务器：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 访问API文档：
http://localhost:8000/docs

## Docker部署

```bash
docker build -t asset-web-backend .
docker run -p 8000:8000 -v /data/nas_data:/data/nas_data:ro asset-web-backend
```

## API接口

- `POST /api/emergency/search` - 搜索告警资产
- `GET /api/emergency/alarm-types` - 获取告警类型
- `GET /api/thumbnail/{asset_id}` - 获取缩略图
- `GET /api/download/{asset_id}` - 下载文件
