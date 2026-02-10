#!/usr/bin/env bash
# QMT Bridge — 后台启动（nohup 模式）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/qmt-bridge.pid"
LOG_FILE="$SCRIPT_DIR/qmt-bridge.log"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[QMT Bridge] 服务已在运行 (PID: $OLD_PID)，请先执行 stop.sh"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo "[QMT Bridge] 启动服务 (后台模式)..."
nohup python server.py "$@" > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

# 等待片刻确认进程存活
sleep 1
if kill -0 "$PID" 2>/dev/null; then
    echo "[QMT Bridge] 服务已启动 (PID: $PID)"
    echo "[QMT Bridge] 日志文件: $LOG_FILE"
    echo "[QMT Bridge] 停止命令: ./stop.sh"
else
    echo "[QMT Bridge] 启动失败，请检查日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
