import paramiko
import os
from dotenv import load_dotenv

def debug_db():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- Logs from coolify-db ---")
    stdin, stdout, stderr = ssh.exec_command("docker logs coolify-db")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    debug_db()
