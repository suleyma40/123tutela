import paramiko
import os
from dotenv import load_dotenv

def check_extensions():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    stdin, stdout, stderr = ssh.exec_command(f"docker exec {container} psql -U postgres -c '\dx'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_extensions()
