@echo off
REM 小神农中医AI - Windows一键启动脚本

echo ========================================
echo   小神农中医AI - Windows启动脚本
echo ========================================

REM 检查Python环境
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    exit /b 1
)

for /f "tokens=*" %%a in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)"') do set PYTHON_VER=%%a
echo   Python版本: %PYTHON_VER%

REM 创建虚拟环境
echo [2/5] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo   虚拟环境创建完成
) else (
    echo   虚拟环境已存在
)

REM 激活虚拟环境
echo [3/5] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [4/5] 安装依赖...
pip install -q --upgrade pip
pip install -q -r backend\requirements.txt

REM 检查模型
echo [5/5] 检查嵌入模型...
if not exist "models\bge-m3" (
    echo   首次启动，下载bge-m3模型（约2GB，可能需要几分钟）...
    if not exist "models" mkdir models
    python -c "from transformers import AutoTokenizer, AutoModel; import os; p='models/bge-m3'; os.makedirs(p,exist_ok=True); AutoTokenizer.from_pretrained('BAAI/bge-m3', trust_remote_code=True).save_pretrained(p); AutoModel.from_pretrained('BAAI/bge-m3', trust_remote_code=True).save_pretrained(p); print('模型下载完成')"
) else (
    echo   模型已存在
)

REM 环境变量由项目根目录 .env 控制（YUNWU_API_KEY、PORT、ADMIN_TOKEN 等）
REM 不再覆盖，确保使用 .env 中的 yunwu.ai 配置

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo   后端API: http://localhost:5001
echo   前端页面: http://localhost:8080
echo   健康检查: http://localhost:5001/api/health
echo   LLM模式: yunwu.ai（由 .env 决定）
echo.
echo   按任意键同时启动后端与前端的本地服务...
pause >nul

REM 启动前端（在新窗口中，避免阻塞后端）
cd frontend
start "小神农前端" python -m http.server 8080
cd ..

REM 启动后端
cd backend
python api_server.py
