import paramiko
import os
from dotenv import load_dotenv

def fix_proxy_permissions():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    print("🔓 Corrigiendo permisos de proxy...")
    # Asegurar que acme.json tenga permisos 600
    ssh.exec_command("touch /data/coolify/proxy/acme.json")
    ssh.exec_command("chmod 600 /data/coolify/proxy/acme.json")
    
    # Intentar cambiar dueño a root (Docker suele usar root para volúmenes a menos que se especifique)
    ssh.exec_command("chown root:root /data/coolify/proxy/acme.json")
    
    # Reiniciar proxy
    print("🔄 Reiniciando Proxy...")
    ssh.exec_command("docker restart coolify-proxy")
    
    ssh.close()

if __name__ == "__main__":
    fix_proxy_permissions()
