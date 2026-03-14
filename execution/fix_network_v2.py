import paramiko
import os
from dotenv import load_dotenv

def fix_network_v2():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🛑 Deteniendo servicios...")
    ssh.exec_command("docker stop $(docker ps -q) || true")
    
    print("🗑️ Eliminando red...")
    ssh.exec_command("docker network rm coolify || true")
    
    print("🌐 Creando red sin IPv6...")
    # Asegurarnos de que no haya rastros de IPv6
    ssh.exec_command("docker network create --driver bridge --ipv6=false coolify")
    
    print("🚀 Iniciando servicios...")
    ssh.exec_command("docker start $(docker ps -a -q) || true")
    
    print("🛰️ Levantando Proxy...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /data/coolify/proxy/docker-compose.yml up -d")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    fix_network_v2()
