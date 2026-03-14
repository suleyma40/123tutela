import paramiko
import os
from dotenv import load_dotenv

def get_proxy_logs():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker logs --tail 100 coolify-proxy")
    # Traefik manda los logs a stderr a veces
    print("--- STDOUT ---")
    print(stdout.read().decode())
    print("--- STDERR ---")
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    get_proxy_logs()
