import paramiko
import os
from dotenv import load_dotenv

def get_coolify_logs():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- Docker Logs (Coolify) ---")
    stdin, stdout, stderr = ssh.exec_command("docker logs --tail 50 coolify")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    get_coolify_logs()
