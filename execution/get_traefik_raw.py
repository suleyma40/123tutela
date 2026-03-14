import paramiko
import os
from dotenv import load_dotenv

def get_traefik_raw():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Obtener toda la configuración que Traefik tiene cargada
    print("--- RAW CONFIG ---")
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- http://localhost:8080/api/rawdata")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    get_traefik_raw()
