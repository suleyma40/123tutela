import paramiko
import os
import json
from dotenv import load_dotenv

def check_priorities():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- http://localhost:8080/api/rawdata")
    data_raw = stdout.read().decode()
    try:
        data = json.loads(data_raw)
        routers = data.get('routers', {})
        
        print("--- ALL ENABLED ROUTERS ---")
        for k, v in routers.items():
            if v.get('status') == 'enabled':
                print(f"Router: {k} | Priority: {v.get('priority')} | Rule: {v.get('rule')}")
    except:
        print("Error")
        
    ssh.close()

if __name__ == "__main__":
    check_priorities()
