import paramiko
import os
import sys
import time
from dotenv import load_dotenv

def deep_clean_reinstall_v4():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Wiping EVERYTHING Docker related to Coolify...")
    wipe_cmds = [
        "docker stop $(docker ps -aq) || true",
        "docker rm $(docker ps -aq) || true",
        "docker volume rm $(docker volume ls -q) || true",
        "docker network rm coolify || true",
        "rm -rf /data/coolify"
    ]
    
    for cmd in wipe_cmds:
        ssh.exec_command(cmd)
        
    print("🚀 Installing Coolify v4 (Official cdn link)...")
    install_cmd = "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash"
    
    # Use interactive shell to send 'y' when prompted and keep it alive
    channel = ssh.invoke_shell()
    channel.send(install_cmd + "\n")
    
    # Wait and respond to prompts
    start_time = time.time()
    while not channel.exit_status_ready():
        if channel.recv_ready():
            out = channel.recv(1024).decode('utf-8', errors='ignore')
            print(out, end="", flush=True)
            
            if "Is this a new installation" in out or "Would you like to install Docker" in out or "confirm" in out.lower():
                channel.send("y\n")
        
        if time.time() - start_time > 900: # 15 minutes
            print("\nTimeout monitoring installation.")
            break
        time.sleep(1)
            
    print("\n✅ Finalized.")
    ssh.close()

if __name__ == "__main__":
    deep_clean_reinstall_v4()
