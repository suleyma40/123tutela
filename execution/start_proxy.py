import paramiko
import os
from dotenv import load_dotenv

def start_proxy():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🚀 Levantando el Proxy (Traefik)...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /data/coolify/proxy/docker-compose.yml up -d")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    start_proxy()
