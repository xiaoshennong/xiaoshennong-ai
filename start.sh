#!/bin/bash
# 小神农中医AI - 一键启动脚本

set -e

echo "========================================"
echo "  小神农中医AI - 启动脚本"
echo "========================================"

# 检查Python环境
echo "[1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "  Python版本: $PYTHON_VERSION"

# 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  虚拟环境创建完成"
else
    echo "  虚拟环境已存在"
fi

# 激活虚拟环境
echo "[3/5] 激活虚拟环境..."
source venv/bin/activate || source venv/Scripts/activate

# 安装依赖
echo "[4/5] 安装依赖..."
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

# 下载嵌入模型（首次启动）
echo "[5/5] 检查嵌入模型..."
if [ ! -d "models/bge-m3" ]; then
    echo "  首次启动，下载bge-m3模型（约2GB，可能需要几分钟）..."
    mkdir -p models
    python3 -c "
from transformers import AutoTokenizer, AutoModel
import os
model_path = 'models/bge-m3'
if not os.path.exists(model_path):
    os.makedirs(model_path, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-m3', trust_remote_code=True)
    model = AutoModel.from_pretrained('BAAI/bge-m3', trust_remote_code=True)
    tokenizer.save_pretrained(model_path)
    model.save_pretrained(model_path)
    print('模型下载完成')
"
else
    echo "  模型已存在"
fi

# 设置环境变量
export LLM_PROVIDER=${LLM_PROVIDER:-mock}
export FLASK_DEBUG=${FLASK_DEBUG:-false}
export PORT=${PORT:-5000}

echo ""
echo "========================================"
echo "  启动完成！"
echo "========================================"
echo "  API地址: http://localhost:$PORT"
echo "  健康检查: http://localhost:$PORT/api/health"
echo "  LLM模式: $LLM_PROVIDER"
echo ""
echo "  常用命令:"
echo "    启动服务: python backend/api_server.py"
echo "    导入数据: python backend/data_pipeline.py --import-all"
echo "    测试辨证: curl -X POST http://localhost:$PORT/api/diagnosis -H 'Content-Type: application/json' -d '{\"symptoms\":\"头痛发热，怕冷\"}'"
echo ""

# 启动服务
cd backend
python api_server.py
