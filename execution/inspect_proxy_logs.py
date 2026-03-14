import paramiko
import os
from dotenv import load_dotenv

def inspect_proxy():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker inspect coolify-proxy --format '{{json .HostConfig.LogConfig}}'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    inspect_proxy()
