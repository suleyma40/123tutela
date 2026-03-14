import paramiko
import os
from dotenv import load_dotenv

def check_mount():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy ls -la /traefik/dynamic/")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_mount()
