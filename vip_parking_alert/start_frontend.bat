@echo off
echo 正在启动VIP车位告警系统前端服务...
cd /d "%~dp0frontend"
npm run dev
pause