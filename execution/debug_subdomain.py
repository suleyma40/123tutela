import paramiko
import os
from dotenv import load_dotenv

def inspect_coolify():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("--- Docker Inspect Coolify (Labels & Networks) ---")
    stdin, stdout, stderr = ssh.exec_command("docker inspect coolify --format '{{json .Config.Labels}} {{json .NetworkSettings.Networks}}'")
    print(stdout.read().decode())
    
    print("\n--- Proxy Logs ---")
    stdin, stdout, stderr = ssh.exec_command("docker logs --tail 50 coolify-proxy")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    inspect_coolify()
