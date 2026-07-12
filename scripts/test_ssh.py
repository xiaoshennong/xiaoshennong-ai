import sys
sys.path.insert(0, 'C:/Users/coins/AppData/Roaming/Python/Python312/site-packages')

import paramiko
import socket

print('paramiko version:', paramiko.__version__)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print('Connecting to 43.247.135.91...')
    client.connect(
        '43.247.135.91',
        username='root',
        password='wKQ1c77r0s7ke',
        timeout=15,
        look_for_keys=False,
        allow_agent=False,
        banner_timeout=15
    )
    print('Connected!')
    
    stdin, stdout, stderr = client.exec_command('echo SSH_SUCCESS && uname -a')
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    print('OUTPUT:', output)
    if error:
        print('STDERR:', error)
    print('SUCCESS!')
    
except paramiko.AuthenticationException as e:
    print('AUTH FAILED:', e)
except socket.timeout:
    print('TIMEOUT')
except Exception as e:
    print('FAILED:', type(e).__name__, str(e))
finally:
    client.close()
    print('Connection closed')
