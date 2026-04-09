#!/bin/bash

echo "🔧 Fixing dependencies and starting services..."

# ============================================
# 检查 Node.js
# ============================================
echo ""
echo "📦 Checking Node.js..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo ""
    echo "Please install Node.js 20+ first:"
    echo ""
    echo "Option 1 - Using Homebrew:"
    echo "  brew install node"
    echo ""
    echo "Option 2 - Using nvm:"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  source ~/.zshrc  # or ~/.bashrc"
    echo "  nvm install 20"
    echo "  nvm use 20"
    echo ""
    echo "Option 3 - Download from https://nodejs.org/"
    echo ""
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version is too old: $(node --version)"
    echo "Please upgrade to Node.js 18+"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# ============================================
# 检查 Python
# ============================================
echo ""
echo "🐍 Checking Python..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# ============================================
# 启动数据库
# ============================================
echo ""
echo "📦 Starting databases..."
docker-compose up -d postgres mongodb redis

echo "⏳ Waiting for databases to be ready..."
sleep 5

# ============================================
# 设置后端
# ============================================
echo ""
echo "🔧 Setting up backend..."

cd apps/api

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖（修复版本问题）
echo "Reinstalling Python dependencies..."
pip install --upgrade pip
pip uninstall -y motor pymongo
pip install pymongo==4.6.2 motor==3.3.2
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

# 启动后端（后台运行）
echo ""
echo "🚀 Starting backend server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

cd ../..

# ============================================
# 设置前端
# ============================================
echo ""
echo "🔧 Setting up frontend..."

cd apps/web

echo "Installing npm dependencies..."
npm install

echo "✅ Frontend dependencies installed"

# 启动前端（后台运行）
echo ""
echo "🚀 Starting frontend server..."
npm run dev &
WEB_PID=$!

cd ../..

# ============================================
# 完成
# ============================================
echo ""
echo "=========================================="
echo "✅ All services started!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API:       http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# 捕获 Ctrl+C 信号
trap "echo ''; echo '🛑 Stopping services...'; kill $API_PID $WEB_PID 2>/dev/null; docker-compose down; exit 0" INT

# 等待进程
wait
