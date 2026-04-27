@echo off
echo 正在启动VIP车位告警系统...

echo 启动后端服务...
start "VIP车位告警系统-后端" cmd /k "cd /d ""%~dp0backend"" && uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo 启动前端服务...
start "VIP车位告警系统-前端" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo 服务启动完成！
echo 后端API: http://localhost:8000
echo 前端页面: http://localhost:3000
echo API文档: http://localhost:8000/docs
pause