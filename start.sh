#!/usr/bin/env bash
# DBM 一键启动脚本（生产模式）
# 构建前端 + 启动后端，单进程单端口提供服务

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 Building frontend..."
cd "$SCRIPT_DIR/frontend"
npm run build

echo "🚀 Starting backend (serving frontend from dist/)..."
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate
python run.py
