import paramiko
import os
from dotenv import load_dotenv

def scan_ports():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Escanear puertos dentro del contenedor
    cmd = "docker exec coolify sh -c 'for p in 80 8080 8000 9000 3000; do (echo > /dev/tcp/127.0.0.1/$p) >/dev/null 2>&1 && echo \"Puerto $p abierto\"; done'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    scan_ports()
