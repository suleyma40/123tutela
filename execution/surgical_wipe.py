import paramiko
import os
from dotenv import load_dotenv

def surgical_wipe():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🛑 Deteniendo servicios...")
    ssh.exec_command("docker stop coolify coolify-db coolify-redis coolify-realtime || true")
    ssh.exec_command("docker rm coolify coolify-db coolify-redis coolify-realtime || true")
    
    print("🗑️ Eliminando volúmenes conflictivos...")
    ssh.exec_command("docker volume rm coolify-db-data coolify-redis-data || true")
    
    print("🚀 Levantando servicios limpios...")
    # El archivo de compose en v4 suele estar en /data/coolify/source/docker-compose.yml
    ssh.exec_command("cd /data/coolify/source && docker compose up -d")
    
    ssh.close()

if __name__ == "__main__":
    surgical_wipe()
