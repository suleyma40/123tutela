import paramiko
import os
import sys
import time
from dotenv import load_dotenv

def install_coolify():
    load_dotenv()
    
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    if not ip or not password:
        print("Error: VPS_IP o VPS_PASSWORD no configurados.")
        sys.exit(1)
        
    print(f"--- Conectando a {user}@{ip} ---")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=20)
        
        print("✅ Conexión establecida.")
        
        # Comando para instalar usando el script oficial pero descargándolo primero
        # Agregamos -f para forzar en caso de problemas
        print("🚀 Iniciando descarga e instalación de Coolify...")
        full_command = (
            "wget -q https://get.coollabs.io/coolify/install.sh -O install.sh && "
            "chmod +x install.sh && "
            "echo 'y' | bash install.sh"
        )
        
        stdin, stdout, stderr = ssh.exec_command(full_command, get_pty=True)
        
        # Leer salida en tiempo real
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end="", flush=True)
            time.sleep(0.5)
            
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"\n✅ Proceso finalizado exitosamente (Código: {exit_status}).")
            print(f"🎉 Dashboard disponible en: http://{ip}:8000")
        else:
            print(f"\n❌ El proceso terminó con error (Código: {exit_status}).")
            print("--- Errores reportados ---")
            print(stderr.read().decode())
            
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    install_coolify()
