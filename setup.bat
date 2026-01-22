@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo ==========================================
echo    环境检查与初始化工具
echo ==========================================
echo.

:: 1. 检查 Node.js
echo [1/4] 正在检查 Node.js 环境...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装: https://nodejs.org/
    goto :ERROR_EXIT
)
echo [成功] Node.js 已安装。

:: 2. 检查 Python
echo [2/4] 正在检查 Python 环境...
set "PYTHON_CMD=python"
python --version >nul 2>&1
if %errorlevel% neq 0 (
    set "PYTHON_CMD=python3"
    python3 --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [错误] 未检测到 Python，请先安装并勾选 "Add Python to PATH"
        goto :ERROR_EXIT
    )
)
echo [成功] Python 已安装。

:: 3. 初始化后端环境
echo.
echo [3/4] 正在初始化后端环境 (Python Venv)...
cd /d "%PROJECT_ROOT%backend"

:: 创建虚拟环境
if not exist ".venv" (
    echo 正在创建虚拟环境...
    %PYTHON_CMD% -m venv .venv
)

:: 配置文件
if not exist ".env" (
    echo 正在从 .env.example 创建 .env 配置文件...
    copy .env.example .env >nul
)

:: 安装依赖
echo 正在安装后端依赖 (可能需要几分钟)...
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 后端依赖安装失败。
    goto :ERROR_EXIT
)

:: 安装 Playwright 浏览器
echo 正在安装 Playwright 浏览器内核...
.venv\Scripts\playwright install chromium
if %errorlevel% neq 0 (
    echo [错误] Playwright 浏览器安装失败。
    goto :ERROR_EXIT
)
echo [成功] 后端环境配置完毕。

:: 4. 初始化前端环境
echo.
echo [4/4] 正在初始化前端环境 (NPM Install)...
cd /d "%PROJECT_ROOT%frontend"
echo 正在安装前端依赖 (可能需要几分钟)...
call npm install
if %errorlevel% neq 0 (
    echo [错误] 前端依赖安装失败。
    goto :ERROR_EXIT
)
echo [成功] 前端环境配置完毕。

echo.
echo ==========================================
echo   全部环境配置完成！
echo   现在可以双击 run.bat 启动项目了。
echo ==========================================
echo.
pause
exit /b 0

:ERROR_EXIT
echo.
echo ------------------------------------------
echo [终止] 配置未完成，请解决上述问题后重试。
echo ------------------------------------------
pause
exit /b 1
