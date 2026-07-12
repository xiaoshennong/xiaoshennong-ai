# 小神农中医AI - 部署指南

## 方案一：使用自有服务器（推荐）

### 1. 购买云服务器

推荐平台：
- **阿里云 ECS**: 2核4G 约 200元/月
- **腾讯云 CVM**: 2核4G 约 180元/月
- **华为云 ECS**: 2核4G 约 190元/月
- **海外VPS**: Vultr/DigitalOcean 2核4G 约 $20/月

### 2. 服务器配置要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 硬盘 | 50GB SSD | 100GB SSD |
| 带宽 | 3Mbps | 5Mbps |
| 系统 | Ubuntu 22.04 | Ubuntu 22.04 |

### 3. 部署步骤

```bash
# 1. SSH登录服务器
ssh root@your-server-ip

# 2. 下载部署脚本
curl -fsSL https://raw.githubusercontent.com/xiaoshennong/xiaoshennong-ai/main/deploy.sh | sudo bash

# 或者手动执行：
git clone https://github.com/xiaoshennong/xiaoshennong-ai.git /opt/xiaoshennong
cd /opt/xiaoshennong
sudo ./deploy.sh
```

### 4. 配置域名和SSL

```bash
# 编辑环境变量
nano /opt/xiaoshennong/.env

# 申请SSL证书（替换为你的域名）
sudo certbot --nginx -d your-domain.com

# 自动续期已配置，无需手动操作
```

## 方案二：使用Render/Railway（零服务器经验）

### Render部署

1. 访问 https://render.com 注册账号
2. 连接GitHub仓库
3. 选择 "Web Service"
4. 配置：
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && python -B api_server.py`
   - 环境变量: 添加 LLM_PROVIDER 和 API Key

### Railway部署

1. 访问 https://railway.app 注册账号
2. 导入GitHub仓库
3. 添加环境变量
4. 自动生成域名

## 方案三：使用阿里云/腾讯云容器服务

```bash
# 阿里云容器镜像服务
# 1. 创建命名空间和镜像仓库
# 2. 构建并推送镜像
docker build -f docker/Dockerfile -t registry.cn-hangzhou.aliyuncs.com/xiaoshennong/api:latest .
docker push registry.cn-hangzhou.aliyuncs.com/xiaoshennong/api:latest

# 3. 在容器服务中部署
# 使用阿里云ACK或腾讯云TKE托管Kubernetes集群
```

## 微信小程序配置

部署完成后，修改小程序前端代码中的API地址：

```javascript
// frontend/pages/diagnosis/diagnosis.js
const API_BASE = 'https://your-domain.com';
```

然后在微信开发者工具中：
1. 开发 → 开发设置 → 服务器域名
2. request合法域名: `https://your-domain.com`
3. uploadFile合法域名: `https://your-domain.com`
4. downloadFile合法域名: `https://your-domain.com`

## 数据迁移

从本地迁移数据到服务器：

```bash
# 本地打包数据
cd /c/Users/coins/xiaoshennong
tar czvf data-backup.tar.gz data/

# 上传到服务器
scp data-backup.tar.gz root@your-server-ip:/opt/xiaoshennong/

# 服务器解压
cd /opt/xiaoshennong
tar xzvf data-backup.tar.gz
docker-compose restart api
```

## 监控与告警

```bash
# 安装基础监控
sudo apt install -y htop iotop

# 查看容器资源使用
docker stats

# 查看API日志
cd /opt/xiaoshennong && docker-compose logs -f api --tail=100
```

## 常见问题

**Q: 服务器内存不足怎么办？**
A: 添加swap分区或升级服务器配置。2核4G是最低要求，推荐4核8G。

**Q: 如何更新部署？**
A: 修改代码后push到GitHub，服务器上执行 `git pull && docker-compose up -d --build`

**Q: 数据库数据会丢失吗？**
A: 不会。数据通过Docker volume挂载到宿主机 `./data/` 目录，容器重建不会丢失。

**Q: 如何备份？**
A: 定期备份 `./data/` 目录即可。建议设置cron定时任务自动备份到对象存储。
