@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PIDFILE=%~dp0.companion.pid"

if "%1"=="stop" goto stop
if "%1"=="status" goto status

:start
if exist "%PIDFILE%" (
    set /p PID=<"%PIDFILE%"
    tasklist /fi "PID eq !PID!" 2>nul | find "!PID!" >nul
    if not errorlevel 1 (
        echo AI Coding Companion 已在运行 (PID: !PID!)
        echo 停止: %~nx0 stop
        pause
        exit /b
    )
    del "%PIDFILE%" 2>nul
)

start "" pythonw main.py 2>nul || start "" python main.py
echo AI Coding Companion 已启动 (后台静默)
echo.
echo 停止: %~nx0 stop
echo 状态: %~nx0 status
timeout /t 5 >nul
exit /b

:stop
if not exist "%PIDFILE%" (
    echo 未在运行 (无 PID 文件)
    pause
    exit /b
)
set /p PID=<"%PIDFILE%"
taskkill /f /pid %PID% >nul 2>&1
del "%PIDFILE%" 2>nul
echo 已停止
timeout /t 3 >nul
exit /b

:status
python -c "import urllib.request, json
try:
 r=json.loads(urllib.request.urlopen('http://127.0.0.1:9599/status',timeout=2).read())
 print(f'状态: {r[\"status\"]}')
 for s in r['sessions']:
  print(f'项目: {s[\"name\"]} ({s[\"state\"]}, {s[\"duration\"]})')
except:
 print('未运行')
" 2>nul
pause
exit /b
