import sys
sys.path.insert(0, 'C:/Users/coins/AppData/Local/Programs/Python/Python313/Lib/site-packages')

import paramiko
import os

HOST = '43.247.135.91'
USER = 'root'
PASSWORD = 'Satoshi2023'
PROJECT_DIR = '/opt/xiaoshennong'

def ssh_exec(cmd, timeout=60):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15, look_for_keys=False, allow_agent=False)
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    exit_code = stdout.channel.recv_exit_status()
    
    client.close()
    return exit_code, output, error

def upload_file(local_path, remote_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15, look_for_keys=False, allow_agent=False)
    
    sftp = client.open_sftp()
    # Ensure remote directory exists
    remote_dir = os.path.dirname(remote_path)
    try:
        sftp.stat(remote_dir)
    except:
        ssh_exec(f'mkdir -p {remote_dir}')
    
    sftp.put(local_path, remote_path)
    sftp.close()
    client.close()
    print(f'Uploaded: {local_path} -> {remote_path}')

print('=== 小神农中医AI - 服务器部署 ===')
print()

# Step 1: Check server and install Docker
print('[1/10] 检查服务器环境...')
rc, out, err = ssh_exec('whoami && docker --version 2>/dev/null || echo NO_DOCKER && docker-compose --version 2>/dev/null || echo NO_COMPOSE')
print(out)

if 'NO_DOCKER' in out:
    print('[1/10] 安装Docker和依赖...')
    rc, out, err = ssh_exec('apt-get update -qq && apt-get install -y -qq docker.io docker-compose git nginx curl', timeout=300)
    if rc == 0:
        print('Docker安装成功')
    else:
        print('Docker安装输出:', err[-500:] if len(err) > 500 else err)

# Step 2: Create project directory
print('[2/10] 创建项目目录...')
rc, out, err = ssh_exec(f'mkdir -p {PROJECT_DIR}/{{backend,frontend,data,logs,nginx,docker}} && ls -la {PROJECT_DIR}')
print('目录创建完成')

# Step 3: Upload docker-compose.yml
print('[3/10] 上传docker-compose.yml...')
docker_compose = '''version: '3.8'
services:
  api:
    build: {context: ., dockerfile: docker/Dockerfile}
    container_name: xiaoshennong-api
    restart: unless-stopped
    ports: ["127.0.0.1:5001:5001"]
    environment:
      - LLM_PROVIDER=mock
      - PORT=5001
      - FLASK_DEBUG=false
    volumes: ["./data:/app/data", "./logs:/app/logs"]
    networks: [xsn-net]
    deploy:
      resources:
        limits: {memory: 4G}
        reservations: {memory: 1G}
  nginx:
    image: nginx:alpine
    container_name: xiaoshennong-nginx
    restart: unless-stopped
    ports: ["80:80"]
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [api]
    networks: [xsn-net]
networks: {xsn-net: {driver: bridge}}'''

with open('C:/Users/coins/xiaoshennong/tmp_deploy/docker-compose.yml', 'w') as f:
    f.write(docker_compose)
upload_file('C:/Users/coins/xiaoshennong/tmp_deploy/docker-compose.yml', f'{PROJECT_DIR}/docker-compose.yml')

# Step 4: Upload Dockerfile
print('[4/10] 上传Dockerfile...')
dockerfile = '''FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ git curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
RUN mkdir -p /app/data/chroma_db_v2 /app/data/agent_data /app/data/cache /app/logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5001
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:5001/api/health || exit 1
EXPOSE 5001
WORKDIR /app/backend
CMD ["python", "-B", "api_server.py"]'''

with open('C:/Users/coins/xiaoshennong/tmp_deploy/Dockerfile', 'w') as f:
    f.write(dockerfile)
upload_file('C:/Users/coins/xiaoshennong/tmp_deploy/Dockerfile', f'{PROJECT_DIR}/docker/Dockerfile')

# Step 5: Upload Nginx config
print('[5/10] 上传Nginx配置...')
nginx_conf = '''server {
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
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        root /usr/share/nginx/html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    access_log /var/log/nginx/xiaoshennong-access.log;
    error_log /var/log/nginx/xiaoshennong-error.log;
}'''

with open('C:/Users/coins/xiaoshennong/tmp_deploy/nginx.conf', 'w') as f:
    f.write(nginx_conf)
upload_file('C:/Users/coins/xiaoshennong/tmp_deploy/nginx.conf', f'{PROJECT_DIR}/nginx/default.conf')

# Step 6: Upload frontend files
print('[6/10] 上传前端文件...')
frontend_dir = '/c/Users/coins/xiaoshennong/frontend'
for filename in ['index.html', 'test_ui_v3.html']:
    local_path = os.path.join(frontend_dir, filename)
    if os.path.exists(local_path):
        upload_file(local_path, f'{PROJECT_DIR}/frontend/{filename}')

# Step 7: Upload backend files
print('[7/10] 上传后端代码...')
backend_dir = '/c/Users/coins/xiaoshennong/backend'
backend_files = [
    'api_server.py', 'rag_engine_v2.py', 'dialogue_engine.py', 'multi_agent_system.py',
    'critical_thinking_engine.py', 'symptom_codes.py', 'syndrome_db.py',
    'contraindication_db.py', 'drug_formula_db.py', 'code_system.py',
    'data_pipeline.py', 'search_engine.py', 'web_crawler_v2.py',
    'llm_client.py', 'llm_client_v2.py', 'llm_client_v3.py', 'llm_client_yunwu.py',
    'requirements.txt'
]

for filename in backend_files:
    local_path = os.path.join(backend_dir, filename)
    if os.path.exists(local_path):
        upload_file(local_path, f'{PROJECT_DIR}/backend/{filename}')

# Step 8: Upload data files
print('[8/10] 上传数据文件...')
data_dir = '/c/Users/coins/xiaoshennong/data'
if os.path.exists(data_dir):
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, data_dir)
            remote_path = f'{PROJECT_DIR}/data/{rel_path}'
            
            # Create remote directory
            remote_dir = os.path.dirname(remote_path)
            ssh_exec(f'mkdir -p {remote_dir}')
            upload_file(local_path, remote_path)

# Step 9: Build and start Docker
print('[9/10] 构建并启动Docker服务...')
rc, out, err = ssh_exec(f'cd {PROJECT_DIR} && docker-compose down 2>/dev/null; docker-compose up -d --build', timeout=300)
if rc == 0:
    print('Docker服务启动成功')
else:
    print('Docker启动错误:', err[-1000:] if len(err) > 1000 else err)

# Step 10: Health check and Nginx config
print('[10/10] 健康检查...')
import time
time.sleep(15)

rc, out, err = ssh_exec(f'curl -s http://localhost:5001/api/health')
if 'status' in out:
    print('API健康检查通过:', out)
else:
    print('API未响应，检查日志...')
    rc, out, err = ssh_exec(f'cd {PROJECT_DIR} && docker-compose logs --tail=30 api')
    print(out[-1000:] if len(out) > 1000 else out)

# Configure Nginx
print('[10/10] 配置Nginx...')
rc, out, err = ssh_exec(f'cp {PROJECT_DIR}/nginx/default.conf /etc/nginx/sites-available/xiaoshennong.conf && ln -sf /etc/nginx/sites-available/xiaoshennong.conf /etc/nginx/sites-enabled/ && rm -f /etc/nginx/sites-enabled/default && nginx -t && systemctl reload nginx')
if rc == 0:
    print('Nginx配置成功')
else:
    print('Nginx配置错误:', err)

print()
print('========================================')
print('  部署完成！')
print('========================================')
print(f'项目目录: {PROJECT_DIR}')
print('API地址:  http://localhost:5001')
print('公网访问: http://43.247.135.91')
print()
print('常用命令:')
print(f'  查看日志: ssh root@{HOST} "cd {PROJECT_DIR} && docker-compose logs -f api"')
print(f'  重启服务: ssh root@{HOST} "cd {PROJECT_DIR} && docker-compose restart"')
print(f'  进入容器: ssh root@{HOST} "cd {PROJECT_DIR} && docker-compose exec api bash"')
print('========================================')
