import paramiko
import os
from dotenv import load_dotenv

def check_vps():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    commands = [
        "lsb_release -a",
        "docker --version",
        "curl --version",
        "free -h"
    ]
    
    for cmd in commands:
        print(f"--- Executing: {cmd} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
    ssh.close()

if __name__ == "__main__":
    check_vps()
