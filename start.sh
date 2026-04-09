#!/bin/bash

# Human.online 启动脚本

echo "🚀 Starting Human.online Development Environment..."

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys before continuing."
    exit 1
fi

# 启动 Docker 服务
echo "📦 Starting Docker services..."
docker-compose up -d

# 等待服务就绪
echo "⏳ Waiting for services to be ready..."
sleep 10

# 检查服务状态
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
