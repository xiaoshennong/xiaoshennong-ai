#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI · 远程服务器部署脚本

用法：
  python scripts/server_deploy.py --host 43.247.135.91 --user root --password Aa123456
"""

import argparse
import os
import tarfile
import tempfile
import paramiko
from pathlib import Path
from datetime import datetime

LOCAL_PROJECT = Path(__file__).parent.parent
REMOTE_PROJECT = "/opt/xiaoshennong"
SERVICE_NAME = "xiaoshennong"

# 需要部署的文件/目录（相对于项目根目录）
DEPLOY_ITEMS = [
    "frontend/index.html",
    "frontend/kg_visual.html",
    "scripts/check_kg.py",
    "scripts/export_kg_for_viz.py",
    "scripts/generate_missing_drugs.py",
    "scripts/kg_enrich_agent.py",
    "scripts/multi_agent_kg_workflow.md",
    "scripts/server_deploy.py",
    "scripts/import_extended_kg.py",
    "scripts/batch_enrich_agents.py",
    "data/kg_graph.json",
    "data/knowledge_graph",
    "backend/requirements.txt",
]


def create_deploy_archive():
    """创建部署压缩包"""
    fd, archive_path = tempfile.mkstemp(suffix=".tar.gz", prefix="xiaoshennong_deploy_")
    os.close(fd)
    archive_path = Path(archive_path)

    with tarfile.open(archive_path, "w:gz") as tar:
        for item in DEPLOY_ITEMS:
            local_path = LOCAL_PROJECT / item
            if not local_path.exists():
                print(f"[WARN] 本地不存在，跳过: {local_path}")
                continue
            tar.add(local_path, arcname=item)

    size_mb = archive_path.stat().st_size / 1024 / 1024
    print(f"[INFO] 部署包已创建: {archive_path} ({size_mb:.2f} MB)")
    return archive_path


def deploy(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"[INFO] 连接服务器 {host} ...")
    client.connect(host, username=user, password=password, timeout=45, look_for_keys=False, allow_agent=False)
    print("[INFO] SSH 连接成功")

    # 上传压缩包
    archive = create_deploy_archive()
    remote_archive = f"/tmp/{archive.name}"
    print(f"[INFO] 上传 {archive.name} ({archive.stat().st_size / 1024 / 1024:.2f} MB) ...")
    sftp = client.open_sftp()
    sftp.put(str(archive), remote_archive)
    sftp.close()
    print("[INFO] 上传完成")

    # 单次执行所有部署命令
    backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{REMOTE_PROJECT}/backups/{backup_name}"

    deploy_script = f"""
set -e
BACKUP_DIR="{backup_dir}"
REMOTE_PROJECT="{REMOTE_PROJECT}"
SERVICE_NAME="{SERVICE_NAME}"
REMOTE_ARCHIVE="{remote_archive}"

echo "[1/7] 备份代码..."
mkdir -p "$BACKUP_DIR"
cd "$REMOTE_PROJECT"
cp -a backend frontend scripts nginx docker deploy.sh start.sh docker-compose.yml .env* README.md DEPLOY.md "$BACKUP_DIR/" 2>/dev/null || true
echo "备份完成: $BACKUP_DIR"

echo "[2/7] 停止服务..."
systemctl stop "$SERVICE_NAME" || true

echo "[3/7] 解压部署包..."
cd "$REMOTE_PROJECT"
tar -xzf "$REMOTE_ARCHIVE" --overwrite
rm -f "$REMOTE_ARCHIVE"

echo "[4/7] 安装依赖..."
"$REMOTE_PROJECT/venv/bin/pip" install -r "$REMOTE_PROJECT/backend/requirements.txt" --upgrade

echo "[5/7] 重新导出知识图谱..."
cd "$REMOTE_PROJECT"
"$REMOTE_PROJECT/venv/bin/python" scripts/export_kg_for_viz.py

echo "[6/7] 启动服务..."
systemctl daemon-reload
systemctl start "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager | head -15

echo "[7/7] 重载 nginx..."
nginx -t && systemctl reload nginx

echo "[CHECK] 等待服务就绪..."
sleep 8
API_CODE=$(curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:5005/api/health || echo "000")
KG_CODE=$(curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1/kg_visual.html || echo "000")
ROOT_CODE=$(curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1/ || echo "000")
echo "API health: $API_CODE"
echo "KG page: $KG_CODE"
echo "Root page: $ROOT_CODE"

if [ "$API_CODE" = "200" ] && [ "$KG_CODE" = "200" ]; then
    echo "[SUCCESS] 部署验证通过"
    exit 0
else
    echo "[WARN] 部署验证未完全通过"
    exit 1
fi
"""

    print("\n[INFO] 在服务器上执行部署脚本（单会话）...")
    stdin, stdout, stderr = client.exec_command(deploy_script, timeout=600, get_pty=True)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    rc = stdout.channel.recv_exit_status()

    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("STDERR:", err[-2000:])

    client.close()

    if rc == 0:
        print("\n[SUCCESS] 部署完成")
        print(f"  主页面: http://{host}/")
        print(f"  知识图谱: http://{host}/kg_visual.html")
        print(f"  API 地址: http://{host}:5005/api/health")
    else:
        print(f"\n[FAILED] 部署脚本退出码: {rc}")
        raise SystemExit(rc)


def main():
    parser = argparse.ArgumentParser(description="小神农远程部署")
    parser.add_argument("--host", default="43.247.135.91")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="Aa123456")
    args = parser.parse_args()

    deploy(args.host, args.user, args.password)


if __name__ == "__main__":
    main()
