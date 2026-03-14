import paramiko
import os
from dotenv import load_dotenv

def check_acme():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("ls -la /data/coolify/proxy/acme.json")
    print(stdout.read().decode())
    
    # Si no existe, lo creamos con permisos correctos
    ssh.exec_command("touch /data/coolify/proxy/acme.json && chmod 600 /data/coolify/proxy/acme.json")
    
    ssh.close()

if __name__ == "__main__":
    check_acme()
