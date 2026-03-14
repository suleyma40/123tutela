import paramiko
import os
from dotenv import load_dotenv

def check_compose_config():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- Docker Compose Config ---")
    stdin, stdout, stderr = ssh.exec_command("cd /data/coolify/source && docker compose config")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_compose_config()
