@echo off
chcp 65001 >nul

echo ==========================================
echo    环境检查与初始化工具
echo ==========================================

echo [1/4] Node 环境检查...
node -v >nul 2>&1 && (echo [成功] Node 已安装) || (echo [失败] 请前往 https://nodejs.org/ 安装 Node.js && pause && exit)

echo [2/4] Python 环境检查...
set "PY=python"
python --version >nul 2>&1 || set "PY=python3"
%PY% --version >nul 2>&1 && (echo [成功] Python 已安装) || (echo [失败] 请前往 https://www.python.org/ 安装 Python 并在安装时勾选 "Add Python to PATH" && pause && exit)

echo [3/4] 部署后端...
cd backend || (echo [失败] 找不到 backend 目录 && pause && exit)
if not exist .venv (
    echo 正在创建虚拟环境...
    %PY% -m venv .venv || (echo [失败] 虚拟环境创建失败 && pause && exit)
)
if not exist .env copy .env.example .env >nul

echo 正在安装后端依赖...
.venv\Scripts\python -m pip install -r requirements.txt || (echo [失败] 后端依赖安装失败 && pause && exit)

echo 正在安装 Playwright 浏览器内核...
.venv\Scripts\python -m playwright install chromium || (echo [失败] Playwright 安装失败 && pause && exit)

echo 正在验证 Playwright 内核状态...
.venv\Scripts\python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True).close(); p.stop()" >nul 2>&1 && (echo [成功] Playwright 已就绪) || (echo [失败] 内核校验未通过，请尝试手动运行: .venv\Scripts\python -m playwright install chromium && pause && exit)

echo [成功] 后端配置完成
cd ..

echo [4/4] 部署前端...
cd frontend || (echo [失败] 找不到 frontend 目录 && pause && exit)
echo 正在安装前端依赖...
call npm install || (echo [失败] 前端依赖安装失败 && pause && exit)
echo [成功] 前端配置完成
cd ..

echo.
echo ==========================================
echo 全部环境配置完成！
echo ==========================================
pause
