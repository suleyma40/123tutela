import paramiko
import os
import json
from dotenv import load_dotenv

def check_coolify_health():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker inspect coolify --format '{{json .State.Health}}'")
    data_raw = stdout.read().decode()
    try:
        data = json.loads(data_raw)
        print(json.dumps(data, indent=2))
    except:
        print(data_raw)
        
    ssh.close()

if __name__ == "__main__":
    check_coolify_health()
