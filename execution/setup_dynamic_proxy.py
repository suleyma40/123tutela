import paramiko
import os
from dotenv import load_dotenv

def create_dynamic_config():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    domain = "panelcoolify.123tutelaapp.com"
    
    config_content = f"""http:
  routers:
    coolify-panel:
      rule: "Host(`{domain}`)"
      entryPoints:
        - https
      service: coolify-panel
      tls:
        certResolver: letsencrypt
  services:
    coolify-panel:
      loadBalancer:
        servers:
          - url: "http://coolify:8080"
"""
    # Escapar comillas invertidas
    safe_content = config_content.replace("`", "\\`")
    
    print(f"🛠️ Creando configuración dinámica en Traefik para {domain}...")
    ssh.exec_command(f"cat <<EOF > /data/coolify/proxy/dynamic/coolify.yml\n{safe_content}\nEOF")
    
    print("🔄 Reiniciando Proxy para asegurar carga...")
    ssh.exec_command("docker restart coolify-proxy")
    
    ssh.close()

if __name__ == "__main__":
    create_dynamic_config()
