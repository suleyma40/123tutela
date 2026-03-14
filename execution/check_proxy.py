import paramiko
import os
from dotenv import load_dotenv

def check_proxy():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("ls -F /data/coolify/proxy")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command("docker ps -a --filter name=coolify-proxy")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_proxy()
