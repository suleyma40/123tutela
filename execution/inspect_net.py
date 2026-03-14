import paramiko
import os
import json
from dotenv import load_dotenv

def inspect_net():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker network inspect coolify")
    data = stdout.read().decode()
    print(data)
    
    ssh.close()

if __name__ == "__main__":
    inspect_net()
