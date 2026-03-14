import paramiko
import os
from dotenv import load_dotenv

def read_proxy_config():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("cat /data/coolify/proxy/docker-compose.yml")
    lines = stdout.readlines()
    for line in lines:
        print(line.strip())
    
    ssh.close()

if __name__ == "__main__":
    read_proxy_config()
