#!/usr/bin/env python3
"""远程部署脚本 - 使用paramiko"""
import paramiko
import sys

HOST = '43.247.135.91'
USER = 'root'
PASSWORD = 'Aa123456'

def run_command(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15, look_for_keys=False, allow_agent=False)
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    
    client.close()
    return output, error

if __name__ == '__main__':
    # 检查服务器状态
    print("[1] 检查服务器状态...")
    out, err = run_command("cd /opt/xiaoshennong && git log --oneline -3 && echo '---' && ls -la backend/*.py | head -10")
    print(out)
    if err:
        print("ERR:", err)
    
    # 拉取最新代码
    print("\n[2] 拉取最新代码...")
    out, err = run_command("cd /opt/xiaoshennong && git stash && git pull origin main 2>&1 || echo 'pull failed'")
    print(out[:500])
    
    # 检查知识库文件
    print("\n[3] 检查知识库数据...")
    out, err = run_command("ls -la /opt/xiaoshennong/data/raw/merged_*.json 2>/dev/null || echo 'No merged files'")
    print(out)
    
    # 复制本地新生成的数据到服务器
    print("\n[4] 数据文件需要手动上传，请使用SFTP")
    print("   sftp -oPasswordAuthentication=yes root@43.247.135.91")
    print("   密码: Aa123456")
    print("   然后: put data/raw/merged_*.json /opt/xiaoshennong/data/raw/")
    print("   然后: put data/raw/medical_cases_batch_*.json /opt/xiaoshennong/data/raw/")
    print("   然后: put data/raw/classical_texts_batch_*.json /opt/xiaoshennong/data/raw/")
    
    # 重启服务
    print("\n[5] 重启API服务...")
    out, err = run_command("systemctl restart xiaoshennong && sleep 2 && systemctl status xiaoshennong --no-pager | head -10")
    print(out)
    
    print("\n[完成] 部署检查完成")
