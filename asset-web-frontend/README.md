# 资产检索系统前端

基于Vue 3的资产检索系统Web界面，科技感深色主题。

## 功能特性

- 🔍 高级搜索（多条件组合）
- 🖼️ 缩略图网格展示
- 📱 响应式设计
- 🌙 科技感深色主题
- ⚡ 快速加载

## 本地开发

1. 安装依赖：
```bash
cd asset-web-frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 访问：http://localhost:8082

## 生产构建

```bash
npm run build
```

## Docker部署

```bash
docker build -t asset-web-frontend .
docker run -p 8082:80 asset-web-frontend
```

##  技术栈

- Vue 3
- Element Plus
- Vue Router
- Axios
- Vite
