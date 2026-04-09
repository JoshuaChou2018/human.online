#!/bin/bash

echo "🔍 Debugging Docker build..."

# 清理旧构建
docker-compose down 2>/dev/null
docker-compose rm -f 2>/dev/null
docker builder prune -f 2>/dev/null

echo ""
echo "🏗️  Building API with verbose output..."
echo ""

# 单独构建 API，显示详细输出
docker-compose build --progress=plain --no-cache api 2>&1 | tee build.log

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed! Last 100 lines of log:"
    echo "=========================================="
    tail -100 build.log
    echo ""
    echo "💡 Common fixes:"
    echo "1. Check your internet connection"
    echo "2. Try: docker system prune -a"
    echo "3. Increase Docker memory limit (if on Mac/Windows)"
else
    echo ""
    echo "✅ API build succeeded! Now building other services..."
    docker-compose build --no-cache web celery
fi
