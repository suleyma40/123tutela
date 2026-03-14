import paramiko
import os
import time
from dotenv import load_dotenv

def run_official_upgrade():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Cleaning up manual config files...")
    ssh.exec_command("rm /data/coolify/source/docker-compose.yml /data/coolify/source/docker-compose.override.yml || true")
    
    print("🚀 Running official upgrade/repair script...")
    # El script de upgrade reconstruye el docker-compose.yml correctamente
    stdin, stdout, stderr = ssh.exec_command("bash /data/coolify/source/upgrade.sh")
    
    # Leer salida
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(1024).decode('utf-8', errors='ignore'), end="", flush=True)
        time.sleep(0.5)
        
    print("\n✅ Script de upgrade finalizado.")
    ssh.close()

if __name__ == "__main__":
    run_official_upgrade()
