import paramiko
import os
import time
from dotenv import load_dotenv

def start_all():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🚀 Iniciando todos los contenedores...")
    ssh.exec_command("docker start coolify-db coolify-redis coolify-realtime coolify-sentinel coolify")
    
    print("⏳ Esperando estabilización (15s)...")
    time.sleep(15)
    
    stdin, stdout, stderr = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    start_all()
