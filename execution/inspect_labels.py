import paramiko
import os
import json
from dotenv import load_dotenv

def find_labels():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Obtenemos las etiquetas de Traefik para ver si Coolify se está registrando
    stdin, stdout, stderr = ssh.exec_command("docker inspect coolify --format '{{json .Config.Labels}}'")
    labels_raw = stdout.read().decode()
    try:
        labels = json.loads(labels_raw)
        print("--- ETIQUETAS DE TRAEFIK EN COOLIFY ---")
        for k, v in labels.items():
            if 'traefik' in k.lower():
                print(f"{k}: {v}")
    except:
        print("No se pudieron leer las etiquetas de forma estructurada.")
        print(labels_raw)
        
    print("\n--- CONFIGURACIÓN DE RED EN COOLIFY ---")
    stdin, stdout, stderr = ssh.exec_command("docker inspect coolify --format '{{json .NetworkSettings.Networks}}'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    find_labels()
