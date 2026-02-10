#!/usr/bin/env bash
# QMT Bridge — 停止服务

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/qmt-bridge.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "[QMT Bridge] PID 文件不存在，服务可能未在运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "[QMT Bridge] 进程 (PID: $PID) 已不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 0
fi

echo "[QMT Bridge] 正在停止服务 (PID: $PID)..."
kill "$PID"

# 等待进程退出，最多 10 秒
for i in $(seq 1 10); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "[QMT Bridge] 服务已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 超时，强制终止
echo "[QMT Bridge] 优雅停止超时，强制终止..."
kill -9 "$PID" 2>/dev/null
rm -f "$PID_FILE"
echo "[QMT Bridge] 服务已强制停止"
