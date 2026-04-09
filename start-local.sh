#!/bin/bash

# 本地开发模式启动脚本（不使用 Docker）

echo "🚀 Starting Human.online in local mode..."

# 检查 .env
if [ ! -f "apps/api/.env" ]; then
    echo "⚠️  Creating .env from template..."
    cp apps/api/.env.example apps/api/.env
    echo "⚠️  Please edit apps/api/.env and add your API keys"
fi

# 只启动数据库（Docker）
echo "📦 Starting databases with Docker..."
docker-compose up -d postgres mongodb redis

# 等待数据库就绪
echo "⏳ Waiting for databases..."
sleep 5

# 检查 Python 环境
cd apps/api

if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

# 验证虚拟环境
if [[ "$(which python)" != *"venv"* ]]; then
    echo "❌ Virtual environment not activated properly!"
    exit 1
fi

echo "📥 Installing Python dependencies..."
python -m pip install -r requirements.txt

echo "🔄 Running database migrations..."
python -m alembic upgrade head 2>/dev/null || echo "⚠️  Migration skipped"

echo "🚀 Starting API server..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

cd ../web

echo "📥 Installing Node dependencies..."
npm install

echo "🚀 Starting Web server..."
npm run dev &
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
