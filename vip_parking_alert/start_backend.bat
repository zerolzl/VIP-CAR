@echo off
echo 正在启动VIP车位告警系统后端服务...
cd /d "%~dp0backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause