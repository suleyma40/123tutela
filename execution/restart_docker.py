import paramiko
import os
from dotenv import load_dotenv

def restart_docker():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🔄 Reiniciando el motor de Docker...")
    ssh.exec_command("systemctl restart docker")
    
    ssh.close()

if __name__ == "__main__":
    restart_docker()
