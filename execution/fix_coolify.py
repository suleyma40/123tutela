import paramiko
import os
from dotenv import load_dotenv

def fix_coolify():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- Intentando reiniciar servicios ---")
    # Comando para forzar la recreación de los contenedores y asegurar que carguen el .env
    commands = [
        "cd /data/coolify/source && docker compose up -d --force-recreate"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    fix_coolify()
