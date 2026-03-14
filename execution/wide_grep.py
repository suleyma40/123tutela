import paramiko
import os
from dotenv import load_dotenv

def wide_grep():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Buscamos la IP problemática en todos los archivos de configuración
    stdin, stdout, stderr = ssh.exec_command("grep -r 'fd3a' /data /etc 2>/dev/null")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    wide_grep()
