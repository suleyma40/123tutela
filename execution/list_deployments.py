import paramiko
import os
from dotenv import load_dotenv

def list_all_containers():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- LISTADO DE CONTENEDORES ---")
    stdin, stdout, stderr = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(stdout.read().decode())
    
    print("\n--- ETIQUETAS TRAEFIK ---")
    stdin, stdout, stderr = ssh.exec_command("docker ps --format '{{.Names}} labels: {{.Labels}}'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    list_all_containers()
