#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "未找到 Docker Compose，请先安装 docker compose 或 docker-compose。"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker 服务未启动，或当前用户没有 Docker 权限。"
  exit 1
fi

mkdir -p logs

echo "正在启动数据资产检索系统..."
"${COMPOSE_CMD[@]}" up -d --build

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "${HOST_IP}" ]; then
  HOST_IP="localhost"
fi

echo
echo "服务启动完成。"
echo "前端系统:     http://${HOST_IP}:8082"
echo "File Browser: http://${HOST_IP}:8081"
echo "后端 API:     http://${HOST_IP}:8003/docs"
echo "pgAdmin:      http://${HOST_IP}:18080"
echo
echo "容器状态："
"${COMPOSE_CMD[@]}" ps
