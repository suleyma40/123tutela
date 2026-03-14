import paramiko
import os
from dotenv import load_dotenv

def final_fix():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🛑 Deteniendo todo...")
    ssh.exec_command("docker stop $(docker ps -aq) || true")
    
    print("🗑️ Limpiando red...")
    ssh.exec_command("docker network rm coolify || true")
    
    print("🩹 Parcheando upgrade.sh para deshabilitar IPv6...")
    ssh.exec_command("sed -i 's/--ipv6//g' /data/coolify/source/upgrade.sh")
    
    print("🌐 Creando red limpia...")
    ssh.exec_command("docker network create --attachable coolify")
    
    print("🚀 Iniciando servicios base...")
    ssh.exec_command("docker start coolify-db coolify-redis coolify-realtime coolify-sentinel coolify")
    
    print("🛰️ Intentando levantar Proxy...")
    # Usamos -f para asegurar que ignore configuraciones previas corruptas
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /data/coolify/proxy/docker-compose.yml up -d --force-recreate")
    
    print("--- Salida Proxy ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    final_fix()
