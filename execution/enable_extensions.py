import paramiko
import os
from dotenv import load_dotenv

def enable_extensions():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # El nombre del contenedor según el listado previo
    container = "bw7aj85ekz1p65w04lptq93j"
    
    print(f"🚀 Activando extensiones en {container}...")
    
    # Comandos para activar PostGIS y PGVector
    commands = [
        f"docker exec {container} psql -U postgres -c 'CREATE EXTENSION IF NOT EXISTS postgis;'",
        f"docker exec {container} psql -U postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out: print(f"Output: {out}")
        if err: print(f"Error: {err}")
    
    ssh.close()

if __name__ == "__main__":
    enable_extensions()
