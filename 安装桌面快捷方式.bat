@echo off
cd /d "%~dp0"
copy /y "AI伴侣仪表盘.url" "%USERPROFILE%\Desktop\AI伴侣仪表盘.url" >nul
echo 已安装桌面快捷方式: AI伴侣仪表盘
echo 双击即可打开仪表盘 (需先启动 daemon: 双击 启动AI伴侣.bat)
pause
