#!/usr/bin/env bash
# QMT Bridge — 前台启动（Ctrl+C 停止）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查是否已在运行
PID_FILE="$SCRIPT_DIR/qmt-bridge.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[QMT Bridge] 服务已在运行 (PID: $OLD_PID)，请先执行 stop.sh"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo "[QMT Bridge] 启动服务 (前台模式)..."
echo "[QMT Bridge] 按 Ctrl+C 停止"

python server.py "$@"
