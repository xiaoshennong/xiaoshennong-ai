# 小神农中医AI - Docker部署配置

## 快速部署指南

### 1. 服务器准备

推荐配置：
- **最低配置**: 2核4G内存，50GB SSD，Ubuntu 22.04
- **推荐配置**: 4核8G内存，100GB SSD，Ubuntu 22.04
- **域名**: 准备已备案域名（国内服务器）或任意域名（海外服务器）

### 2. 一键部署

```bash
# 克隆代码
git clone https://github.com/xiaoshennong/xiaoshennong-ai.git
cd xiaoshennong-ai

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 3. 手动部署步骤

#### 3.1 安装Docker和Docker Compose

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

#### 3.2 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API Key和域名
nano .env
```

#### 3.3 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### 4. 配置Nginx和SSL（生产环境）

```bash
# 安装Nginx和Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# 复制Nginx配置
sudo cp nginx/xiaoshennong.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/xiaoshennong.conf /etc/nginx/sites-enabled/

# 申请SSL证书
sudo certbot --nginx -d your-domain.com

# 重启Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LLM_PROVIDER` | 否 | `mock` | LLM提供商: mock/yunwu/kimi-code/deepseek/openai |
| `YUNWU_API_KEY` | 条件 | - | Yunwu AI API Key |
| `KIMI_API_KEY` | 条件 | - | Kimi API Key |
| `DEEPSEEK_API_KEY` | 条件 | - | DeepSeek API Key |
| `OPENAI_API_KEY` | 条件 | - | OpenAI API Key |
| `DOMAIN` | 是 | - | 你的域名 |
| `PORT` | 否 | 5001 | API服务端口 |

## 目录结构

```
xiaoshennong-ai/
├── backend/          # Python后端代码
├── frontend/         # 前端静态文件
├── data/             # 数据文件（会被挂载到容器）
├── docker/           # Docker配置文件
│   ├── Dockerfile
│   └── entrypoint.sh
├── nginx/            # Nginx配置
│   └── xiaoshennong.conf
├── docker-compose.yml
├── .env.example
└── deploy.sh         # 一键部署脚本
```

## 数据持久化

以下数据会持久化到宿主机：
- `./data/chroma_db_v2/` - 向量数据库
- `./data/agent_data/` - Agent数据
- `./data/cache/` - 缓存数据
- `./logs/` - 日志文件

## 监控与维护

```bash
# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats

# 重启单个服务
docker-compose restart api

# 进入容器调试
docker-compose exec api bash

# 备份数据
tar czvf backup-$(date +%Y%m%d).tar.gz data/
```

## 故障排查

| 问题 | 排查命令 |
|------|----------|
| 服务无法启动 | `docker-compose logs api` |
| 端口被占用 | `sudo lsof -i :5001` |
| Nginx 502错误 | `sudo nginx -t && sudo tail -f /var/log/nginx/error.log` |
| 数据库损坏 | `docker-compose down && rm -rf data/chroma_db_v2 && docker-compose up -d` |

## 安全建议

1. **修改默认端口**: 生产环境建议修改docker-compose.yml中的端口映射
2. **防火墙配置**: 只开放80/443端口，关闭5001外部访问
3. **定期备份**: 设置cron定时备份data目录
4. **日志轮转**: 配置logrotate防止日志文件过大
5. **API限流**: 生产环境建议添加Nginx限流配置

## 联系支持

- GitHub Issues: https://github.com/xiaoshennong/xiaoshennong-ai/issues
- 项目文档: https://github.com/xiaoshennong/xiaoshennong-ai/blob/main/README.md
