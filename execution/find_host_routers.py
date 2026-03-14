import paramiko
import os
import json
from dotenv import load_dotenv

def find_host_routers():
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
        
        print("--- ALL HOST RULES ---")
        for k, v in routers.items():
            rule = v.get('rule', '')
            if 'Host' in rule:
                print(f"Router: {k} | Rule: {rule}")
    except:
        print("Error al decodificar JSON")
        
    ssh.close()

if __name__ == "__main__":
    find_host_routers()
