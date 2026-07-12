import sys
sys.path.insert(0, 'C:/Users/coins/AppData/Local/Programs/Python/Python313/Lib/site-packages')

import paramiko
import socket

print('Python version:', sys.version.split()[0])

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print('Connecting to 43.247.135.91...')
    client.connect(
        '43.247.135.91',
        port=22,
        username='root',
        password='wKQ1c77r0s7ke',
        timeout=15,
        banner_timeout=15,
        auth_timeout=15,
        look_for_keys=False,
        allow_agent=False
    )
    print('SSH CONNECTED!')
    
    # Quick test
    stdin, stdout, stderr = client.exec_command('whoami')
    print('User:', stdout.read().decode().strip())
    
    # Check if Docker is installed
    stdin, stdout, stderr = client.exec_command('docker --version 2>/dev/null || echo NO_DOCKER')
    docker_check = stdout.read().decode().strip()
    print('Docker:', docker_check)
    
    if 'NO_DOCKER' in docker_check:
        print('Installing Docker...')
        stdin, stdout, stderr = client.exec_command(
            'apt-get update -qq && apt-get install -y -qq docker.io docker-compose git nginx curl',
            timeout=300
        )
        output = stdout.read().decode('utf-8', errors='replace').strip()
        error = stderr.read().decode('utf-8', errors='replace').strip()
        print('Install output:', output[-500:] if len(output) > 500 else output)
        if error:
            print('Install errors:', error[-300:] if len(error) > 300 else error)
    
    # Create project directory
    print('Creating project directory...')
    stdin, stdout, stderr = client.exec_command('mkdir -p /opt/xiaoshennong && ls -la /opt/xiaoshennong')
    print('Project dir:', stdout.read().decode().strip())
    
    print('\n=== SERVER IS READY ===')
    print('Next: Upload code with scp or git clone')
    
except paramiko.AuthenticationException as e:
    print('AUTH FAILED:', str(e))
except socket.timeout:
    print('TIMEOUT')
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
    import traceback
    traceback.print_exc()
finally:
    client.close()
    print('Connection closed')
