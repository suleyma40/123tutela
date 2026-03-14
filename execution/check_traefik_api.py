import paramiko
import os
import json
from dotenv import load_dotenv

def check_traefik_api():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- http://localhost:8080/api/http/routers")
    data = stdout.read().decode()
    try:
        routers = json.loads(data)
        print("--- TRAEFIK ROUTERS ---")
        for r in routers:
            if 'coolify' in r['name']:
                print(json.dumps(r, indent=2))
    except:
        print(data)
        
    ssh.close()

if __name__ == "__main__":
    check_traefik_api()
