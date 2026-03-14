import paramiko
import os
from dotenv import load_dotenv

def test_root_dashboard():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Probar el root del panel
    cmd = "docker exec coolify-proxy wget -qS --header='Host: panelcoolify.123tutelaapp.com' http://172.16.16.5:8080/ 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    test_root_dashboard()
