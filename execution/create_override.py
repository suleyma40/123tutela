import paramiko
import os
from dotenv import load_dotenv

def create_override():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    domain = "panelcoolify.123tutelaapp.com"
    
    override_content = f"""services:
  coolify:
    labels:
      - traefik.enable=true
      - traefik.http.routers.coolify.rule=Host(`{domain}`)
      - traefik.http.routers.coolify.entrypoints=https
      - traefik.http.routers.coolify.tls=true
      - traefik.http.routers.coolify.tls.certresolver=letsencrypt
      - traefik.http.services.coolify.loadbalancer.server.port=8080
"""
    
    # Escapar comillas invertidas
    safe_content = override_content.replace("`", "\\`")
    
    print("📝 Creando docker-compose.override.yml...")
    ssh.exec_command(f"cat <<EOF > /data/coolify/source/docker-compose.override.yml\n{safe_content}\nEOF")
    
    # Forzar recreación
    print("🔄 Aplicando cambios con force-recreate...")
    stdin, stdout, stderr = ssh.exec_command("cd /data/coolify/source && docker compose up -d --force-recreate")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    create_override()
