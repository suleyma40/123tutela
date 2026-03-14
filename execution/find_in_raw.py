import paramiko
import os
import json
from dotenv import load_dotenv

def find_coolify_in_raw():
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
        services = data.get('services', {})
        
        print("--- ROUTERS ENCONTRADOS ---")
        for k, v in routers.items():
            if 'coolify' in k:
                print(f"Router: {k}")
                print(json.dumps(v, indent=2))
                
        print("\n--- SERVICES ENCONTRADOS ---")
        for k, v in services.items():
            if 'coolify' in k:
                print(f"Service: {k}")
                print(json.dumps(v, indent=2))
    except:
        print("Error al decodificar JSON")
        
    ssh.close()

if __name__ == "__main__":
    find_coolify_in_raw()
