import paramiko
import os
from dotenv import load_dotenv

def inspect_n8n_labels():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Buscar el contenedor de n8n aunque esté detenido
    cmd = "docker ps -a --filter 'name=n8n' --format '{{.Names}}\t{{.Labels}}'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    inspect_n8n_labels()
