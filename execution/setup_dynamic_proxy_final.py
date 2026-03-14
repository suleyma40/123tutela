import paramiko
import os
from dotenv import load_dotenv

def update_dynamic_config_name():
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
    coolify-panel-secure:
      rule: "Host(`{domain}`)"
      entryPoints:
        - https
      service: coolify-panel
      tls:
        certResolver: letsencrypt
    coolify-panel-http:
      rule: "Host(`{domain}`)"
      entryPoints:
        - http
      middlewares:
        - redirect-to-https
      service: coolify-panel
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true
  services:
    coolify-panel:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: "http://coolify:8080"
"""
    safe_content = config_content.replace("`", "\\`")
    ssh.exec_command(f"cat <<EOF > /data/coolify/proxy/dynamic/coolify.yml\n{safe_content}\nEOF")
    ssh.exec_command("docker restart coolify-proxy")
    
    ssh.close()

if __name__ == "__main__":
    update_dynamic_config_name()
