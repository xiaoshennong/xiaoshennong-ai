#!/bin/bash
# 小神农中医AI - Ubuntu服务器一键部署脚本
# 在服务器上直接执行: bash <(curl -s https://raw.githubusercontent.com/xiaoshennong/xiaoshennong-ai/main/deploy.sh)
# 或者下载后执行: chmod +x deploy.sh && sudo ./deploy.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "========================================"
echo "  小神农中医AI - 服务器部署脚本"
echo "========================================"
echo ""

# 步骤1: 检查root权限
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 sudo 或 root 用户运行此脚本"
    exit 1
fi

# 步骤2: 更新系统
print_info "更新系统包..."
apt-get update -qq
apt-get upgrade -y -qq
print_success "系统更新完成"

# 步骤3: 安装基础依赖
print_info "安装基础依赖..."
apt-get install -y -qq curl wget git vim nginx certbot python3-certbot-nginx ufw htop
print_success "基础依赖安装完成"

# 步骤4: 安装Docker
print_info "安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ${SUDO_USER:-$USER} 2>/dev/null || true
    systemctl enable docker
    systemctl start docker
    print_success "Docker安装完成"
else
    print_warning "Docker已安装，跳过"
fi

# 步骤5: 安装Docker Compose
print_info "安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y -qq docker-compose
    print_success "Docker Compose安装完成"
else
    print_warning "Docker Compose已安装，跳过"
fi

# 步骤6: 配置防火墙
print_info "配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
print_success "防火墙配置完成（已开放80/443/SSH）"

# 步骤7: 创建项目目录
print_info "创建项目目录..."
PROJECT_DIR="/opt/xiaoshennong"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/data/chroma_db_v2
mkdir -p $PROJECT_DIR/data/agent_data
mkdir -p $PROJECT_DIR/data/cache
mkdir -p $PROJECT_DIR/nginx/ssl
print_success "项目目录创建完成: $PROJECT_DIR"

# 步骤8: 获取代码
print_info "获取项目代码..."
cd $PROJECT_DIR

# 尝试从GitHub克隆
if ! git clone https://github.com/xiaoshennong/xiaoshennong-ai.git /tmp/xsn-code 2>/dev/null; then
    print_warning "GitHub克隆失败，将创建基础部署文件..."
    
    # 创建docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: xiaoshennong-api
    restart: unless-stopped
    ports:
      - "127.0.0.1:5001:5001"
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER:-mock}
      - YUNWU_API_KEY=${YUNWU_API_KEY:-}
      - KIMI_API_KEY=${KIMI_API_KEY:-}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - PORT=5001
      - FLASK_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - xiaoshennong-network
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G

  nginx:
    image: nginx:alpine
    container_name: xiaoshennong-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./nginx/xiaoshennong.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
    networks:
      - xiaoshennong-network

networks:
  xiaoshennong-network:
    driver: bridge
EOF

    # 创建Dockerfile
    mkdir -p docker
    cat > docker/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ git curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
RUN mkdir -p /app/data/chroma_db_v2 /app/data/agent_data /app/data/cache /app/logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5001
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1
EXPOSE 5001
WORKDIR /app/backend
CMD ["python", "-B", "api_server.py"]
EOF

    # 创建Nginx配置
    mkdir -p nginx
    cat > nginx/xiaoshennong.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        root /usr/share/nginx/html;
        index index.html test_ui_v3.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://api:5001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
        proxy_cache off;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        root /usr/share/nginx/html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    access_log /var/log/nginx/xiaoshennong-access.log;
    error_log /var/log/nginx/xiaoshennong-error.log;
}
EOF

    # 创建前端目录和基础HTML
    mkdir -p frontend
    cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小神农中医AI</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif; 
               background: #f8f5f0; color: #333; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #4a7c59; }
        .status { padding: 20px; background: white; border-radius: 8px; margin: 20px 0; }
        .btn { display: inline-block; padding: 12px 24px; background: #4a7c59; color: white; 
               text-decoration: none; border-radius: 4px; margin: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>小神农中医AI</h1>
        <p>服务器部署成功</p>
        <div class="status">
            <p>API状态: <span id="api-status">检查中...</span></p>
        </div>
        <a href="/test_ui_v3.html" class="btn">进入测试UI</a>
        <a href="/api/health" class="btn">API健康检查</a>
    </div>
    <script>
        fetch('/api/health')
            .then(r => r.json())
            .then(d => document.getElementById('api-status').textContent = '运行中')
            .catch(e => document.getElementById('api-status').textContent = '未启动');
    </script>
</body>
</html>
EOF

    # 创建.env.example
    cat > .env.example << 'EOF'
LLM_PROVIDER=mock
YUNWU_API_KEY=
KIMI_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
PORT=5001
DOMAIN=
FLASK_DEBUG=false
EOF

    print_success "基础部署文件创建完成"
else
    cp -r /tmp/xsn-code/* .
    rm -rf /tmp/xsn-code
    print_success "代码从GitHub克隆完成"
fi

# 步骤9: 配置环境变量
print_info "配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "请编辑 $PROJECT_DIR/.env 文件，填入你的API Key"
fi

# 步骤10: 创建后端目录结构（如果没有代码）
if [ ! -d "backend" ]; then
    print_info "创建后端基础代码..."
    mkdir -p backend
    
    # 创建requirements.txt
    cat > backend/requirements.txt << 'EOF'
flask>=2.3.0
flask-cors>=4.0.0
chromadb>=0.4.0
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
EOF

    # 创建基础API服务器
    cat > backend/api_server.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0.0", "mode": "deployed"})

@app.route("/api/diagnosis", methods=["POST"])
def diagnosis():
    return jsonify({"success": True, "data": {"message": "API运行中，请导入完整代码"}})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
EOF

    print_success "后端基础代码创建完成"
fi

# 步骤11: 构建并启动Docker服务
print_info "构建Docker镜像..."
docker-compose build --no-cache

print_info "启动服务..."
docker-compose up -d

# 等待服务启动
print_info "等待服务启动（约30秒）..."
sleep 30

# 步骤12: 健康检查
print_info "进行健康检查..."
if curl -sf http://localhost:5001/api/health > /dev/null 2>&1; then
    print_success "API服务运行正常"
else
    print_warning "API服务可能尚未完全启动，检查日志:"
    docker-compose logs --tail=20 api
fi

# 步骤13: 配置Nginx
print_info "配置Nginx..."
if [ -f "$PROJECT_DIR/nginx/xiaoshennong.conf" ]; then
    cp $PROJECT_DIR/nginx/xiaoshennong.conf /etc/nginx/sites-available/
    
    if [ ! -L /etc/nginx/sites-enabled/xiaoshennong.conf ]; then
        ln -s /etc/nginx/sites-available/xiaoshennong.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
    fi
    
    # 移除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t && systemctl reload nginx
    print_success "Nginx配置完成"
fi

# 步骤14: 显示部署信息
echo ""
echo "========================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "API地址:  http://localhost:5001"
echo "公网访问: http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo ""
echo "常用命令:"
echo "  查看日志:    cd $PROJECT_DIR && docker-compose logs -f api"
echo "  重启服务:    cd $PROJECT_DIR && docker-compose restart"
echo "  停止服务:    cd $PROJECT_DIR && docker-compose down"
echo ""
echo "下一步:"
echo "  1. 编辑环境变量: nano $PROJECT_DIR/.env"
echo "  2. 配置域名DNS指向服务器IP: $(curl -s ifconfig.me 2>/dev/null || echo '查看服务器IP')"
echo "  3. 申请SSL证书: certbot --nginx -d your-domain.com"
echo "  4. 上传完整代码到 $PROJECT_DIR/backend/ 和 $PROJECT_DIR/frontend/"
echo ""
echo "========================================"
