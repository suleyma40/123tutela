import paramiko
import os
import base64
from dotenv import load_dotenv

def read_panel_env():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("base64 /data/coolify/source/.env")
    b64_data = stdout.read().decode().replace("\n", "").replace("\r", "")
    data = base64.b64decode(b64_data).decode('utf-8')
    print(data)
    
    ssh.close()

if __name__ == "__main__":
    read_panel_env()
