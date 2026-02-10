@echo off
chcp 65001 >nul 2>&1
REM QMT Bridge — 停止服务

cd /d "%~dp0"

set "PID_FILE=%~dp0qmt-bridge.pid"

if not exist "%PID_FILE%" (
    echo [QMT Bridge] PID 文件不存在，服务可能未在运行
    exit /b 0
)

set /p PID=<"%PID_FILE%"

REM 检查进程是否存在
tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [QMT Bridge] 进程 (PID: %PID%) 已不存在，清理 PID 文件
    del /f "%PID_FILE%" >nul 2>&1
    exit /b 0
)

echo [QMT Bridge] 正在停止服务 (PID: %PID%)...

REM 优雅终止：先尝试 taskkill，再强制
taskkill /pid %PID% >nul 2>&1

REM 等待进程退出，最多 10 秒
for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul 2>&1
    if errorlevel 1 (
        echo [QMT Bridge] 服务已停止
        del /f "%PID_FILE%" >nul 2>&1
        exit /b 0
    )
)

REM 超时，强制终止
echo [QMT Bridge] 优雅停止超时，强制终止...
taskkill /f /pid %PID% >nul 2>&1
del /f "%PID_FILE%" >nul 2>&1
echo [QMT Bridge] 服务已强制停止
