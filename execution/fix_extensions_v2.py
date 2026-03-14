import paramiko
import os
from dotenv import load_dotenv

def fix_extensions():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    print("🛠 Preparando base de datos...")
    
    # Crear el rol supabase_admin si no existe, ya que las extensiones de esta imagen lo requieren
    setup_cmds = [
        f"docker exec {container} psql -U postgres -c \"CREATE ROLE supabase_admin WITH SUPERUSER NOINHERIT;\"",
        f"docker exec {container} psql -U postgres -c \"CREATE EXTENSION IF NOT EXISTS postgis;\"",
        f"docker exec {container} psql -U postgres -c \"CREATE EXTENSION IF NOT EXISTS vector;\""
    ]
    
    for cmd in setup_cmds:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(f"Cmd: {cmd}")
        print(stdout.read().decode())
        print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    fix_extensions()
