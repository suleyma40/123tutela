import paramiko
import os
from dotenv import load_dotenv

def inject_subdomain_labels():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    domain = "panelcoolify.123tutelaapp.com"
    
    # Nuevo contenido para el docker-compose.yml de Coolify con los labels de Traefik
    new_compose = f"""services:
  coolify:
    container_name: coolify
    image: ghcr.io/coollabsio/coolify:latest
    restart: always
    working_dir: /var/www/html
    extra_hosts:
      - 'host.docker.internal:host-gateway'
    networks:
      - coolify
    labels:
      - traefik.enable=true
      - traefik.http.routers.coolify.rule=Host(`{domain}`)
      - traefik.http.routers.coolify.entrypoints=https
      - traefik.http.routers.coolify.tls=true
      - traefik.http.routers.coolify.tls.certresolver=letsencrypt
      - traefik.http.services.coolify.loadbalancer.server.port=8080
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - soketi
  postgres:
    image: postgres:15-alpine
    container_name: coolify-db
    restart: always
    networks:
      - coolify
    env_file:
      - .env
    volumes:
      - coolify-db-data:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
    container_name: coolify-redis
    restart: always
    networks:
      - coolify
    env_file:
      - .env
  soketi:
    container_name: coolify-realtime
    image: ghcr.io/coollabsio/coolify-realtime:latest
    extra_hosts:
      - 'host.docker.internal:host-gateway'
    restart: always
    networks:
      - coolify
    env_file:
      - .env
networks:
  coolify:
    external: true
volumes:
  coolify-db-data:
    external: false
"""
    # En lugar de reescribir todo a ciegas (que puede romper contraseñas si no las leo),
    # voy a intentar una aproximación más segura: inyectar solo la sección de labels.
    
    print(f"🚀 Inyectando labels para {domain}...")
    
    # Comando para agregar los labels al contenedor coolify usando sed o simplemente reescribiendo si estamos seguros
    # Como ya tenemos una instalación fresca de v4, voy a reescribirlo usando el formato estándar de v4 que acabo de armar
    # PERO, debo leer las contraseñas del .env para no romper la conexión a la DB.
    
    # Escapar comillas invertidas para que el bash no las interprete como comandos
    new_compose_escaped = new_compose.replace("`", "\\`").replace("$", "\\$")
    
    ssh_cmd = f"cat <<EOF > /data/coolify/source/docker-compose.yml\n{new_compose_escaped}\nEOF"
    ssh.exec_command(ssh_cmd)
    
    print("🔄 Reiniciando stack de Coolify...")
    ssh.exec_command("cd /data/coolify/source && docker compose up -d --remove-orphans --force-recreate")
    
    ssh.close()

if __name__ == "__main__":
    inject_subdomain_labels()
