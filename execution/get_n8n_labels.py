import paramiko
import os
import json
from dotenv import load_dotenv

def get_n8n_labels():
    load_dotenv()
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker inspect n8n-qz0q1cpj5gsxua74auj69rcs --format '{{json .Config.Labels}}'")
    data_raw = stdout.read().decode()
    try:
        labels = json.loads(data_raw)
        print("--- N8N LABELS ---")
        for k, v in labels.items():
            if 'traefik' in k:
                print(f"{k}: {v}")
    except:
        print(data_raw)
    
    ssh.close()

if __name__ == "__main__":
    get_n8n_labels()
