@echo off
chcp 65001 >nul 2>&1
REM QMT Bridge — 后台启动（类 nohup 模式）
REM 使用 PowerShell Start-Process 实现后台隐藏运行，关闭控制台窗口后进程不会终止。

cd /d "%~dp0.."

set "PID_FILE=%cd%\qmt-bridge.pid"
set "LOG_FILE=%cd%\qmt-bridge.log"

REM 检查是否已在运行
if exist "%PID_FILE%" (
    set /p OLD_PID=<"%PID_FILE%"
    call :check_pid
    if errorlevel 1 goto :eof
)

echo [QMT Bridge] 启动服务 (后台模式)...

REM 使用 PowerShell 以隐藏窗口方式启动进程
powershell -NoProfile -Command ^
  "$p = Start-Process -FilePath qmt-server -ArgumentList '%*' ^
    -WindowStyle Hidden ^
    -RedirectStandardOutput '%LOG_FILE%' ^
    -RedirectStandardError '%cd%\qmt-bridge-error.log' ^
    -PassThru; ^
  $p.Id | Out-File -Encoding ascii -NoNewline '%PID_FILE%'"

REM 等待 1 秒确认进程存活
timeout /t 1 /nobreak >nul

if not exist "%PID_FILE%" (
    echo [QMT Bridge] 启动失败，PID 文件未生成
    exit /b 1
)

set /p PID=<"%PID_FILE%"
tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul 2>&1
if %errorlevel%==0 (
    echo [QMT Bridge] 服务已启动 (PID: %PID%)
    echo [QMT Bridge] 日志文件: %LOG_FILE%
    echo [QMT Bridge] 停止命令: scripts\stop.bat
) else (
    echo [QMT Bridge] 启动失败，请检查日志: %LOG_FILE%
    del /f "%PID_FILE%" >nul 2>&1
    exit /b 1
)
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
