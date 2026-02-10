@echo off
chcp 65001 >nul 2>&1
REM QMT Bridge — 前台启动（Ctrl+C 停止）

cd /d "%~dp0.."

REM 检查是否已在运行
set "PID_FILE=%cd%\qmt-bridge.pid"
if exist "%PID_FILE%" (
    set /p OLD_PID=<"%PID_FILE%"
    call :check_pid
)

echo [QMT Bridge] 启动服务 (前台模式)...
echo [QMT Bridge] 按 Ctrl+C 停止

qmt-server %*
goto :eof

:check_pid
setlocal
set /p PID=<"%PID_FILE%"
tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul 2>&1
if %errorlevel%==0 (
    echo [QMT Bridge] 服务已在运行 (PID: %PID%)，请先执行 scripts\stop.bat
    exit /b 1
) else (
    del /f "%PID_FILE%" >nul 2>&1
)
endlocal
goto :eof
