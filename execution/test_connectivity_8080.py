import paramiko
import os
from dotenv import load_dotenv

def test_connectivity_8080():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Probar si el proxy puede ver al panel en el puerto 8080
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- --header='Host: panelcoolify.123tutelaapp.com' http://coolify:8080/api/health")
    print("--- Test Puerto 8080 ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    test_connectivity_8080()
