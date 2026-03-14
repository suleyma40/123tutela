import paramiko
import os
from dotenv import load_dotenv

def final_push():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Cleaning one last time...")
    ssh.exec_command("docker stop coolify coolify-db coolify-redis coolify-realtime || true")
    ssh.exec_command("docker rm coolify coolify-db coolify-redis coolify-realtime || true")
    ssh.exec_command("rm -rf /data/coolify")
    
    print("🚀 Running simplified installer...")
    # This combination usually works for bash scripts that expect simple interaction
    cmd = "curl -fsSL https://get.coollabs.io/coolify/install.sh | bash -s -- -f"
    
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    stdin.write("y\n")
    stdin.flush()
    
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(1024).decode('utf-8', errors='ignore'), end="", flush=True)
            
    print("\n✅ Done.")
    ssh.close()

if __name__ == "__main__":
    final_push()
