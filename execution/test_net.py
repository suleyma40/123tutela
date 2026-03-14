import paramiko
import os
from dotenv import load_dotenv

def test_net():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    ssh.exec_command("docker network create test-net")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect test-net")
    print(stdout.read().decode())
    ssh.exec_command("docker network rm test-net")
    
    ssh.close()

if __name__ == "__main__":
    test_net()
