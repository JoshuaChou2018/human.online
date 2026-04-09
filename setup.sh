#!/bin/bash

echo "🚀 Setting up Human.online development environment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before continuing."
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

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

cd ../..

# Setup Frontend
echo "📦 Setting up Node.js frontend..."
cd apps/web

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

cd ../..

# Make scripts executable
chmod +x start.sh

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your OpenAI API key"
echo "   2. Start services with: ./start.sh"
echo "   3. Or start manually:"
echo "      - Backend: cd apps/api && source venv/bin/activate && uvicorn main:app --reload"
echo "      - Frontend: cd apps/web && npm run dev"
echo ""
