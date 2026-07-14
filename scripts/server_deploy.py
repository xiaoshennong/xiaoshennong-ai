#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农中医AI · 远程服务器部署脚本

用法：
  python scripts/server_deploy.py --host 43.247.135.91 --user root --password Aa123456
"""

import argparse
import os
import sys
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
    "data/kg_graph.json",
    "data/knowledge_graph",
    "backend/requirements.txt",
]


def run_remote(client, cmd, timeout=60):
    """在远程执行命令并返回输出"""
    print(f"\n[REMOTE] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out.strip():
        print(out[:2000])
    if err.strip():
        print("STDERR:", err[:1000])
    rc = stdout.channel.recv_exit_status()
    if rc != 0:
        print(f"Command failed with rc={rc}")
    return rc, out, err


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
    client.connect(host, username=user, password=password, timeout=20, look_for_keys=False, allow_agent=False)
    print("[INFO] SSH 连接成功")

    # 1. 备份
    backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{REMOTE_PROJECT}/backups/{backup_name}"
    rc, _, _ = run_remote(client, f"mkdir -p {backup_dir} && cp -a {REMOTE_PROJECT}/. {backup_dir}/ 2>/dev/null || true", timeout=120)
    if rc == 0:
        print(f"[INFO] 已备份到 {backup_dir}")

    # 2. 停止服务
    run_remote(client, f"systemctl stop {SERVICE_NAME}", timeout=30)

    # 3. 上传并解压
    archive = create_deploy_archive()
    remote_archive = f"/tmp/{archive.name}"
    print(f"[INFO] 上传 {archive.name} 到 {remote_archive} ...")
    sftp = client.open_sftp()
    sftp.put(str(archive), remote_archive)
    sftp.close()
    print("[INFO] 上传完成")

    # 解压到项目目录
    run_remote(client, f"cd {REMOTE_PROJECT} && tar -xzf {remote_archive} --overwrite", timeout=120)
    run_remote(client, f"rm -f {remote_archive}")

    # 4. 安装依赖
    venv_pip = f"{REMOTE_PROJECT}/venv/bin/pip"
    req_file = f"{REMOTE_PROJECT}/backend/requirements.txt"
    run_remote(client, f"{venv_pip} install -r {req_file} --upgrade", timeout=180)

    # 5. 重新生成 kg_graph.json（确保服务器上数据一致）
    venv_python = f"{REMOTE_PROJECT}/venv/bin/python"
    run_remote(client, f"cd {REMOTE_PROJECT} && {venv_python} scripts/export_kg_for_viz.py", timeout=120)

    # 6. 启动服务
    run_remote(client, f"systemctl daemon-reload && systemctl start {SERVICE_NAME}", timeout=30)
    run_remote(client, f"systemctl status {SERVICE_NAME} --no-pager | head -20", timeout=10)

    # 7. 重载 nginx
    run_remote(client, "nginx -t && systemctl reload nginx", timeout=30)

    # 8. 健康检查
    print("\n[INFO] 等待服务启动 ...")
    import time
    time.sleep(5)
    rc, out, err = run_remote(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:5005/api/health", timeout=15)
    if rc == 0 and out.strip() == "200":
        print("[SUCCESS] 后端健康检查通过")
    else:
        print(f"[WARN] 后端健康检查异常: {out}")

    rc, out, err = run_remote(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1/frontend/kg_visual.html", timeout=15)
    if rc == 0 and out.strip() == "200":
        print("[SUCCESS] 前端知识图谱页面可访问")
    else:
        print(f"[WARN] 前端页面检查异常: {out}")

    client.close()
    print("\n[SUCCESS] 部署完成")
    print(f"  访问地址: http://{host}/frontend/kg_visual.html")
    print(f"  API 地址: http://{host}/api/health")


def main():
    parser = argparse.ArgumentParser(description="小神农远程部署")
    parser.add_argument("--host", default="43.247.135.91")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="Aa123456")
    args = parser.parse_args()

    deploy(args.host, args.user, args.password)


if __name__ == "__main__":
    main()
