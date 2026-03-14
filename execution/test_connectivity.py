import paramiko
import os
from dotenv import load_dotenv

def test_connectivity():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Probar si el proxy puede ver al panel en el puerto 80
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- http://coolify:80/health")
    print("--- Test Puerto 80 ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Probar puerto 8000 (v3 usaba este, v4 a veces también)
    stdin, stdout, stderr = ssh.exec_command("docker exec coolify-proxy wget -qO- http://coolify:8000/health")
    print("--- Test Puerto 8000 ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    test_connectivity()
