#!/bin/bash

set -e

echo "🚀 Setting up Human.online development environment..."
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/redhat-release ]; then
        OS="redhat"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo "📋 Detected OS: $OS"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install system dependencies
echo ""
echo "🔍 Checking system dependencies..."

# Check Git
if ! command_exists git; then
    echo "⚠️  Git not found. Installing..."
    if [ "$OS" == "debian" ]; then
        sudo apt-get update && sudo apt-get install -y git
    elif [ "$OS" == "redhat" ]; then
        sudo yum install -y git
    elif [ "$OS" == "macos" ]; then
        echo "Please install Git first: brew install git"
        exit 1
    else
        echo "❌ Please install Git manually"
        exit 1
    fi
fi
echo "✅ Git is installed"

# Check Python 3
if ! command_exists python3; then
    echo "⚠️  Python 3 not found. Installing..."
    if [ "$OS" == "debian" ]; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif [ "$OS" == "redhat" ]; then
        sudo yum install -y python3 python3-pip
    elif [ "$OS" == "macos" ]; then
        echo "Please install Python 3 first: brew install python@3.12"
        exit 1
    else
        echo "❌ Please install Python 3.10+ manually from https://python.org"
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "⚠️  Python $PYTHON_VERSION found, but 3.10+ is recommended"
    echo "Continuing anyway, but you may encounter issues..."
    sleep 2
fi
echo "✅ Python 3 is installed ($PYTHON_VERSION)"

# Check Node.js
if ! command_exists node; then
    echo "⚠️  Node.js not found. Installing..."
    if [ "$OS" == "debian" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [ "$OS" == "redhat" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs
    elif [ "$OS" == "macos" ]; then
        echo "Please install Node.js first: brew install node@20"
        exit 1
    else
        echo "❌ Please install Node.js 20+ manually from https://nodejs.org"
        exit 1
    fi
fi

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d. -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "⚠️  Node.js $(node --version) found, but 20+ is required"
    echo "Please upgrade Node.js"
    exit 1
fi
echo "✅ Node.js is installed ($(node --version))"

# Check Docker (optional but recommended)
if ! command_exists docker; then
    echo "⚠️  Docker not found. It's optional but recommended for running databases."
    echo "   You can install it later from: https://docs.docker.com/get-docker/"
    sleep 2
else
    echo "✅ Docker is installed"
fi

echo ""
echo "📦 Installing project dependencies..."
echo ""

# Check if .env exists
if [ ! -f "apps/api/.env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp apps/api/.env.example apps/api/.env
    echo "⚠️  Please edit apps/api/.env file with your API keys before starting services."
    echo ""
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p apps/api/uploads
mkdir -p logs

# Setup Backend
echo "🐍 Setting up Python backend..."
cd apps/api

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
if ! pip install -r requirements.txt; then
    echo "❌ Failed to install Python dependencies"
    echo "You may need to install system build tools:"
    if [ "$OS" == "debian" ]; then
        echo "  sudo apt-get install -y python3-dev build-essential"
    elif [ "$OS" == "redhat" ]; then
        echo "  sudo yum install -y python3-devel gcc"
    elif [ "$OS" == "macos" ]; then
        echo "  xcode-select --install"
    fi
    exit 1
fi

cd ../..

# Setup Frontend
echo ""
echo "📦 Setting up Node.js frontend..."
cd apps/web

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    if ! npm install; then
        echo "❌ Failed to install Node.js dependencies"
        exit 1
    fi
else
    echo "Node modules already exist, skipping npm install"
fi

cd ../..

# Make scripts executable
chmod +x start-local.sh 2>/dev/null || true
chmod +x fix-and-start.sh 2>/dev/null || true

echo ""
echo "============================================"
echo "✅ Setup completed successfully!"
echo "============================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. 📝 Configure API Keys:"
echo "   Edit: apps/api/.env"
echo "   Add at least one LLM API key:"
echo "     - OPENAI_API_KEY (https://platform.openai.com)"
echo "     - KIMI_API_KEY (https://platform.moonshot.cn)"
echo "     - DEEPSEEK_API_KEY (https://platform.deepseek.com)"
echo ""
echo "2. 🗄️  Start Databases (Docker):"
echo "   docker-compose up -d postgres mongodb redis"
echo ""
echo "3. 🚀 Start Services:"
echo "   bash start-local.sh"
echo ""
echo "4. 🌐 Access Application:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Tips:"
echo "   - Use DeepSeek for best cost-effectiveness"
echo "   - Check API docs for testing endpoints"
echo ""
