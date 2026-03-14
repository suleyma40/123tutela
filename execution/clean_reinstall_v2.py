import paramiko
import os
from dotenv import load_dotenv

def clean_reinstall_v2():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🧹 Limpiando instalación previa de forma profunda...")
    clean_cmds = [
        "docker stop $(docker ps -a -q --filter name=coolify) || true",
        "docker rm $(docker ps -a -q --filter name=coolify) || true",
        "docker volume rm $(docker volume ls -q --filter name=coolify) || true",
        "rm -rf /data/coolify"
    ]
    
    for cmd in clean_cmds:
        ssh.exec_command(cmd)
        
    print("🚀 Reinstalando Coolify con Pipe 'yes'...")
    # Usar yes para responder afirmativamente a todas las preguntas del script
    install_cmd = "curl -fsSL https://get.coollabs.io/coolify/install.sh | yes y | bash"
    
    stdin, stdout, stderr = ssh.exec_command(install_cmd, get_pty=True)
    
    # Mostrar salida
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(1024).decode('utf-8', errors='ignore'), end="", flush=True)
            
    print("\n✅ Proceso terminado.")
    ssh.close()

if __name__ == "__main__":
    clean_reinstall_v2()
