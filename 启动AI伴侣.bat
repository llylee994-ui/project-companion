@echo off
cd /d "%~dp0"
start "" python main.py --no-browser
timeout /t 2 >nul
start http://127.0.0.1:9599
