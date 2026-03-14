import paramiko
import os
from dotenv import load_dotenv

def get_real_logs():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Capturar logs a un archivo y leerlo
    ssh.exec_command("docker logs coolify-proxy > /tmp/proxy_logs 2>&1")
    stdin, stdout, stderr = ssh.exec_command("cat /tmp/proxy_logs")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    get_real_logs()
