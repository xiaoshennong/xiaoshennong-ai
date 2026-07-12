#!/bin/bash
# 小神农中医AI - 一键部署脚本
# 支持：Ubuntu 20.04/22.04, Debian 11/12

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 sudo 运行此脚本"
    exit 1
fi

echo "========================================"
echo "  小神农中医AI - 服务器部署脚本"
echo "========================================"
echo ""

# 步骤1：检查系统
print_info "检查操作系统..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
    print_success "检测到: $OS $VERSION"
else
    print_error "无法识别操作系统"
    exit 1
fi

# 步骤2：安装基础依赖
print_info "安装基础依赖..."
apt-get update -qq
apt-get install -y -qq curl wget git vim nginx certbot python3-certbot-nginx ufw
print_success "基础依赖安装完成"

# 步骤3：安装Docker
print_info "安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ${SUDO_USER:-$USER}
    systemctl enable docker
    systemctl start docker
    print_success "Docker安装完成"
else
    print_warning "Docker已安装，跳过"
fi

# 步骤4：安装Docker Compose
print_info "安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y -qq docker-compose
    print_success "Docker Compose安装完成"
else
    print_warning "Docker Compose已安装，跳过"
fi

# 步骤5：配置防火墙
print_info "配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
print_success "防火墙配置完成（已开放80/443/SSH）"

# 步骤6：创建项目目录
print_info "创建项目目录..."
PROJECT_DIR="/opt/xiaoshennong"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/data/chroma_db_v2
mkdir -p $PROJECT_DIR/data/agent_data
mkdir -p $PROJECT_DIR/data/cache
mkdir -p $PROJECT_DIR/nginx/ssl
print_success "项目目录创建完成: $PROJECT_DIR"

# 步骤7：获取代码
print_info "获取项目代码..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd $PROJECT_DIR
    git pull origin main
    print_success "代码已更新"
else
    # 如果当前目录是项目目录，复制过去
    if [ -f "docker-compose.yml" ]; then
        cp -r . $PROJECT_DIR/
        print_success "代码已复制到 $PROJECT_DIR"
    else
        git clone https://github.com/xiaoshennong/xiaoshennong-ai.git $PROJECT_DIR
        print_success "代码已克隆"
    fi
fi

# 步骤8：配置环境变量
print_info "配置环境变量..."
cd $PROJECT_DIR
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "请编辑 $PROJECT_DIR/.env 文件，填入你的API Key和域名"
    print_warning "命令: nano $PROJECT_DIR/.env"
fi

# 步骤9：构建并启动服务
print_info "构建Docker镜像..."
cd $PROJECT_DIR
docker-compose build --no-cache

print_info "启动服务..."
docker-compose up -d

# 等待服务启动
print_info "等待服务启动（约30秒）..."
sleep 30

# 步骤10：健康检查
print_info "进行健康检查..."
if curl -sf http://localhost:5001/api/health > /dev/null 2>&1; then
    print_success "API服务运行正常"
else
    print_warning "API服务可能尚未完全启动，请检查日志: docker-compose logs api"
fi

# 步骤11：配置Nginx
print_info "配置Nginx..."
if [ -f "$PROJECT_DIR/nginx/xiaoshennong.conf" ]; then
    cp $PROJECT_DIR/nginx/xiaoshennong.conf /etc/nginx/sites-available/
    
    # 如果配置了域名，替换模板中的域名
    if [ -f "$PROJECT_DIR/.env" ]; then
        DOMAIN=$(grep -E '^DOMAIN=' $PROJECT_DIR/.env | cut -d= -f2 | tr -d '"')
        if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "your-domain.com" ]; then
            sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/xiaoshennong.conf
            print_success "Nginx域名已配置: $DOMAIN"
        fi
    fi
    
    # 启用站点
    if [ ! -L /etc/nginx/sites-enabled/xiaoshennong.conf ]; then
        ln -s /etc/nginx/sites-available/xiaoshennong.conf /etc/nginx/sites-enabled/
    fi
    
    # 测试并重载
    nginx -t && systemctl reload nginx
    print_success "Nginx配置完成"
else
    print_warning "Nginx配置文件不存在，跳过"
fi

# 步骤12：显示部署信息
echo ""
echo "========================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "API地址:  http://localhost:5001"
echo "前端地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo ""
echo "常用命令:"
echo "  查看日志:    cd $PROJECT_DIR && docker-compose logs -f api"
echo "  重启服务:    cd $PROJECT_DIR && docker-compose restart"
echo "  更新代码:    cd $PROJECT_DIR && git pull && docker-compose up -d --build"
echo "  停止服务:    cd $PROJECT_DIR && docker-compose down"
echo ""
echo "下一步:"
echo "  1. 编辑环境变量: nano $PROJECT_DIR/.env"
echo "  2. 配置域名DNS指向服务器IP"
echo "  3. 申请SSL证书: certbot --nginx -d your-domain.com"
echo "  4. 导入古籍数据到知识库"
echo ""
echo "========================================"
