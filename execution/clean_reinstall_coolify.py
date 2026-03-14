import paramiko
import os
import sys
import time
from dotenv import load_dotenv

def clean_reinstall():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Limpiando instalación previa...")
    # Detener y eliminar contenedores y volúmenes de Coolify
    clean_cmds = [
        "docker stop coolify coolify-db coolify-redis coolify-realtime || true",
        "docker rm coolify coolify-db coolify-redis coolify-realtime || true",
        "docker volume rm coolify-db-data coolify-redis-data || true",
        "rm -rf /data/coolify"
    ]
    
    for cmd in clean_cmds:
        ssh.exec_command(cmd)
        
    print("🚀 Reinstalando Coolify desde cero...")
    install_cmd = "curl -fsSL https://get.coollabs.io/coolify/install.sh | bash"
    
    # Usar shell interactiva para asegurar que la instalación proceda sin pararse
    channel = ssh.invoke_shell()
    channel.send(install_cmd + "\n")
    
    # Esperar de forma inteligente
    start_time = time.time()
    while not channel.exit_status_ready():
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8', errors='ignore')
            print(data, end="", flush=True)
            
        if "Is this a new installation?" in data:
            channel.send("y\n")
            
        if time.time() - start_time > 600: # 10 min
            print("\nTimeout en reinstalación.")
            break
        time.sleep(0.5)
        
    print("\n✅ Reinstalación completa.")
    ssh.close()

if __name__ == "__main__":
    clean_reinstall()
