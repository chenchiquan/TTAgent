#!/bin/bash
# 部署脚本：拉最新镜像 + 重启容器 + 清理旧镜像
# 用法（Linux/WSL/Git Bash）: ./deploy.sh
# Windows PowerShell 可直接手动跑两条:
#   docker-compose pull
#   docker-compose up -d
set -e
cd "$(dirname "$0")"

echo "==> 拉取最新镜像..."
docker-compose pull

echo "==> 启动/重启容器..."
docker-compose up -d

echo "==> 清理旧镜像..."
docker image prune -f

echo "==> 部署完成，访问 http://localhost"
