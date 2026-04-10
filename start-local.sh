#!/bin/bash

# 本地开发模式启动脚本

# 检查 .env
if [ ! -f "apps/api/.env" ]; then
    echo "⚠️  Creating .env from template..."
    cp apps/api/.env.example apps/api/.env
    echo "⚠️  Please edit apps/api/.env and add your API keys"
fi

# 只启动数据库（Docker）
echo "📦 Starting databases with Docker..."
docker-compose up -d postgres mongodb redis

# 设置数据库容器自动重启策略（防止意外停止）
echo "🔧 Setting restart policy for databases..."
docker update --restart=unless-stopped humanonline-postgres 2>/dev/null || true
docker update --restart=unless-stopped humanonline-mongodb 2>/dev/null || true
docker update --restart=unless-stopped humanonline-redis 2>/dev/null || true

# 等待数据库就绪
echo "⏳ Waiting for databases..."
sleep 5

# 创建 PostgreSQL 数据库（如果不存在）
echo "🗄️  Creating database if not exists..."
docker exec humanonline-postgres psql -U postgres -c "CREATE DATABASE humanonline;" 2>/dev/null || echo "Database already exists or will be created by migrations"

# 检查 Python 环境
cd apps/api

if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

# 验证虚拟环境 (检查 pip list 是否能运行)
if ! python -c "import sys; sys.exit(0 if 'venv' in sys.executable else 1)" 2>/dev/null; then
    echo "⚠️  Virtual environment check warning, continuing anyway..."
fi

echo "Python path: $(which python)"

echo "📥 Installing Python dependencies..."
python -m pip install -r requirements.txt

echo "🔄 Running database migrations..."
python -m alembic upgrade head 2>/dev/null || echo "⚠️  Migration skipped"

echo "🎭 Initializing celebrity avatars (if not exists)..."
python scripts/init_celebrity_avatars.py 2>/dev/null || echo "⚠️  Celebrity avatars init skipped (optional)"

echo "🚀 Starting API server..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

cd ../web

echo "📥 Installing Node dependencies..."
npm install

echo "🚀 Starting Web server..."
# 增加 Node.js 内存限制，启用 Turbopack 加速编译
NODE_OPTIONS="--max-old-space-size=4096" npm run dev &
WEB_PID=$!

echo ""
echo "=========================================="
echo "✅ Services started!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API:       http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# 等待中断
wait $API_PID $WEB_PID
