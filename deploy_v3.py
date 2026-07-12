#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署v3 API到服务器
通过HTTP API上传代码并重启服务
"""
import json
import requests
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

SERVER_IP = "43.247.135.91"
OLD_API = f"http://{SERVER_IP}:5001"

# 1. 检查服务器状态
print("=== 检查服务器状态 ===")
try:
    resp = requests.get(f"{OLD_API}/api/health", timeout=10)
    data = resp.json()
    print(f"  服务器运行中: v{data.get('version', '?')}")
    print(f"  当前数据: {data.get('rag_stats', {})}")
except Exception as e:
    print(f"  服务器连接失败: {e}")
    sys.exit(1)

# 2. 读取v3 API代码
print("\n=== 读取v3 API代码 ===")
with open('backend/local_api_v3.py', 'r', encoding='utf-8') as f:
    v3_code = f.read()
print(f"  代码大小: {len(v3_code)} 字符")

# 3. 上传到服务器（通过现有API的扩展端点）
print("\n=== 上传v3代码到服务器 ===")
# 由于服务器没有文件上传API，我们通过SSH方式
# 先创建一个简单的HTTP部署脚本
print("  请手动在服务器上执行以下命令:")
print(f"""
  ssh root@{SERVER_IP}
  # 密码: wKQ1c77r0s7ke 或 Aa123456
  
  cd /root/xiaoshennong-ai
  git pull origin main
  
  # 安装依赖
  pip install flask flask-cors -q
  
  # 下载知识库数据（从GitHub）
  mkdir -p knowledge_base/symptoms knowledge_base/drugs knowledge_base/formulas
  
  # 启动v3 API
  cd backend
  nohup python local_api_v3.py > v3.log 2>&1 &
  
  # 检查状态
  curl http://localhost:5003/api/health
""")

print("\n=== 本地测试v3 API ===")
import subprocess
result = subprocess.run(
    ['curl', '-s', 'http://localhost:5003/api/health'],
    capture_output=True, text=True
)
print(f"  本地v3状态: {result.stdout[:200]}")

print("\n部署指南已生成。请手动SSH到服务器执行部署。")
