import paramiko
import os
from dotenv import load_dotenv

def fix_network():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🛑 Deteniendo servicios dependientes...")
    ssh.exec_command("docker stop coolify coolify-db coolify-redis coolify-realtime coolify-sentinel || true")
    
    print("🗑️ Eliminando red con problemas de IPv6...")
    ssh.exec_command("docker network rm coolify || true")
    
    print("🌐 Creando red nueva (Solo IPv4)...")
    ssh.exec_command("docker network create --driver bridge coolify")
    
    print("🚀 Reiniciando servicios...")
    ssh.exec_command("docker start coolify-db coolify-redis coolify-realtime coolify-sentinel coolify")
    
    print("🛰️ Intentando levantar el Proxy nuevamente...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /data/coolify/proxy/docker-compose.yml up -d")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    fix_network()
