#!/usr/bin/env python3
"""SSH连接脚本 - 用于部署服务器"""
import subprocess
import sys
import os

HOST = "43.247.135.91"
USER = "root"
PASSWORD = "wKQ1c77r0s7ke"
PORT = 22

def ssh_command(cmd):
    """执行SSH命令"""
    ssh_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        f"{USER}@{HOST}",
        cmd
    ]
    
    # 使用pexpect风格的交互
    import pty
    import select
    import termios
    import tty
    
    master_fd, slave_fd = pty.openpty()
    
    proc = subprocess.Popen(
        ssh_cmd,
        stdin=slave_fd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    os.close(slave_fd)
    
    output = ""
    password_sent = False
    
    while True:
        ready, _, _ = select.select([master_fd, proc.stdout, proc.stderr], [], [], 30)
        
        if not ready:
            break
            
        for fd in ready:
            if fd == master_fd:
                try:
                    data = os.read(master_fd, 1024).decode('utf-8', errors='replace')
                    output += data
                    if "password:" in data.lower() and not password_sent:
                        os.write(master_fd, (PASSWORD + "\n").encode())
                        password_sent = True
                except:
                    pass
            elif fd == proc.stdout:
                data = fd.read(1024)
                if data:
                    output += data
                    print(data, end='', file=sys.stdout)
            elif fd == proc.stderr:
                data = fd.read(1024)
                if data:
                    output += data
                    print(data, end='', file=sys.stderr)
        
        if proc.poll() is not None:
            break
    
    os.close(master_fd)
    return proc.returncode, output

if __name__ == "__main__":
    print(f"Connecting to {HOST} as {USER}...")
    rc, output = ssh_command("echo 'SSH_CONNECTION_SUCCESS'")
    print(f"\nReturn code: {rc}")
    if rc == 0 and "SSH_CONNECTION_SUCCESS" in output:
        print("Connection successful!")
    else:
        print("Connection failed.")
        print("Output:", output[-500:] if len(output) > 500 else output)
