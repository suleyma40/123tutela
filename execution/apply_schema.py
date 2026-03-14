import paramiko
import os
from dotenv import load_dotenv

def apply_schema():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    sql_file = "execution/schema_123tutela.sql"
    
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # Escapar comillas simples para el comando shell
    sql_content_escaped = sql_content.replace("'", "'\\''")
    
    print(f"🚀 Aplicando esquema SQL en {container}...")
    cmd = f"docker exec {container} psql -U postgres -c '{sql_content_escaped}'"
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if out: print(f"Output: {out}")
    if err: print(f"Error: {err}")
    
    ssh.close()

if __name__ == "__main__":
    apply_schema()
