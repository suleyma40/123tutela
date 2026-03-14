import paramiko
import os
from dotenv import load_dotenv

def apply_labels_safe():
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
    safe_content = override_content.replace("`", "\\`")
    ssh.exec_command(f"cat <<EOF > /data/coolify/source/docker-compose.override.yml\n{safe_content}\nEOF")
    
    # IMPORTANTE: Usar --env-file .env y docker-compose.prod.yml + override
    print("🔄 Aplicando cambios de forma segura...")
    cmd = "cd /data/coolify/source && docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env up -d"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    apply_labels_safe()
