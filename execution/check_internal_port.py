import paramiko
import os
from dotenv import load_dotenv

def check_internal_port():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Ver qué procesos están escuchando dentro del contenedor
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify netstat -ptln")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_internal_port()
