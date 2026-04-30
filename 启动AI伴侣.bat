@echo off
cd /d "%~dp0"

if "%1"=="stop" goto stop
if "%1"=="status" goto status

:start
rem 检查是否已在运行
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9599/health',timeout=2)" >nul 2>&1
if not errorlevel 1 (
    echo AI Coding Companion 已在运行
    echo 停止请运行: %~nx0 stop
    pause
    exit /b
)

rem 后台启动
start "" pythonw "%~dp0main.py"
echo AI Coding Companion 已启动 ^(后台静默^)
echo.
echo 查看状态: %~nx0 status
echo 停止后台: %~nx0 stop
echo.
pause
exit /b

:stop
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9599/health',timeout=2)" >nul 2>&1
if errorlevel 1 (
    echo 未在运行
    pause
    exit /b
)
rem 通过 daemon 自身的 PID 文件来杀
if exist "%~dp0.companion.pid" (
    set /p PID=<"%~dp0.companion.pid"
    taskkill /f /pid !PID! >nul 2>&1
    del "%~dp0.companion.pid" 2>nul
)
echo 已停止
pause
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
