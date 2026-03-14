import paramiko
import os
import sys
import time
from dotenv import load_dotenv

def install_v4_final():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Deep clean before v4 installation...")
    # Detener todos los contenedores posibles de coolify v3 o v4 fallida
    clean_cmds = [
        "docker stop $(docker ps -aq) || true",
        "docker rm $(docker ps -aq) || true",
        "docker volume rm $(docker volume ls -q) || true",
        "rm -rf /data/coolify"
    ]
    
    for cmd in clean_cmds:
        ssh.exec_command(cmd)
        
    print("🚀 Installing Coolify v4 (Official)...")
    # v4 link
    v4_url = "https://cdn.coollabs.io/coolify/install.sh"
    # El instalador de v4 tiene un flag -f para forzar configuración pero usualmente no requiere interacciones si docker ya está
    cmd = f"curl -fsSL {v4_url} | bash"
    
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    
    # El instalador de v4 a veces pide confirmación para instalar Docker si no está, o para sobreescribir.
    # Enviamos 'y' preventivo.
    stdin.write("y\n")
    stdin.flush()
    
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(1024).decode('utf-8', errors='ignore'), end="", flush=True)
        time.sleep(1)
            
    print("\n✅ v4 Installation process finished.")
    ssh.close()

if __name__ == "__main__":
    install_v4_final()
