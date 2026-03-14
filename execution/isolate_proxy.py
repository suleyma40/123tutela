import paramiko
import os
from dotenv import load_dotenv

def isolate_proxy():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🛑 Deteniendo contenedor Coolify...")
    ssh.exec_command("docker stop coolify")
    
    print("🗑️ Recreando red...")
    ssh.exec_command("docker network rm coolify")
    ssh.exec_command("docker network create --driver bridge coolify")
    
    print("🛰️ Intentando levantar Proxy SOLO...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /data/coolify/proxy/docker-compose.yml up -d")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    isolate_proxy()
