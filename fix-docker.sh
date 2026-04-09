#!/bin/bash

echo "🔧 Fixing Docker build issues..."

# 停止现有容器
echo "🛑 Stopping existing containers..."
docker-compose down

# 清理构建缓存
echo "🧹 Cleaning build cache..."
docker-compose rm -f
docker builder prune -f

# 删除旧的镜像
echo "🗑️  Removing old images..."
docker rmi humanonline-web humanonline-api humanonline-celery 2>/dev/null || true

# 重新构建
echo "🏗️  Rebuilding containers..."
docker-compose build --no-cache

# 启动服务
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Fix applied! Waiting for services to start..."
sleep 10

# 检查状态
docker-compose ps

echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
