import paramiko
import os
import time
from dotenv import load_dotenv

def get_proxy_logs_shell():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    channel = ssh.invoke_shell()
    channel.send("docker logs coolify-proxy\n")
    time.sleep(2)
    while channel.recv_ready():
        print(channel.recv(1024).decode('utf-8', errors='ignore'), end="")
    
    ssh.close()

if __name__ == "__main__":
    get_proxy_logs_shell()
