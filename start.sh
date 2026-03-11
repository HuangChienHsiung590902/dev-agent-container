#!/bin/bash
# =============================================================================
# Startup Script for Dev Agent Container
# =============================================================================

echo "=========================================="
echo "Dev Agent Container Starting..."
echo "=========================================="

# 進入工作目錄
cd /home/agent/workspace

# 啟動 Agent API Server (背景執行)
echo "[1/2] Starting Agent API Server..."
python3 agent_api.py > /home/agent/agent_api.log 2>&1 &
API_PID=$!
echo "Agent API started (PID: $API_PID)"

# 等待 API 啟動
sleep 3

# 可選: 啟動 Docker daemon (DinD)
# 如果需要 Docker-in-Docker 功能，取消註釋以下行:
# dockerd > /home/agent/dockerd.log 2>&1 &

echo "[2/2] Setup complete!"
echo ""
echo "=========================================="
echo "Services:"
echo "  - Agent API:  http://localhost:8000"
echo "  - API Docs:   http://localhost:8000/docs"
echo "  - Jupyter:    http://localhost:8888"
echo "=========================================="
echo ""
echo "To access container: docker exec -it dev-agent bash"
echo ""

# 保持容器執行
tail -f /dev/null
