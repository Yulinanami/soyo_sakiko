@echo off
chcp 65001 >nul
setlocal

:: 获取脚本所在目录
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo [Soyo Saki] 正在启动聚合搜索器...

:: 启动后端
echo [1/2] 正在新的窗口启动后端服务 (FastAPI)...
start "SoyoSaki-Backend" cmd /c "cd /d backend && .venv\Scripts\activate && uvicorn app.main:app --reload"

:: 启动前端
echo [2/2] 正在新的窗口启动前端服务 (Vite)...
start "SoyoSaki-Frontend" cmd /c "cd /d frontend && npm run dev"

echo.
echo ==========================================
echo 程序已启动
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo.
echo 正在为您打开浏览器...
echo ==========================================
echo.
:: 等待 3 秒确保 Vite 已经开始监听
timeout /t 2 /nobreak >nul
start http://localhost:5173
pause
