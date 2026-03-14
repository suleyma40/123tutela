import json
import os
import paramiko
from dotenv import load_dotenv

def chunk_text(text, limit=1500):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < limit:
            current_chunk += p + "\n"
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = p + "\n"
    if current_chunk: chunks.append(current_chunk.strip())
    return chunks

def insert_knowledge():
    load_dotenv()
    with open(".tmp/documentation_analysis.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    knowledge_text = data['legal_base']
    chunks = chunk_text(knowledge_text)
    
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    print(f"📥 Cargando {len(chunks)} fragmentos de conocimiento legal...")
    
    for i, chunk in enumerate(chunks):
        title = f"Motor Jurídico - Parte {i+1}"
        # Escapar comillas para SQL
        chunk_esc = chunk.replace("'", "''")
        
        sql = f"INSERT INTO conocimiento_legal (titulo, contenido, fuente) VALUES ('{title}', '{chunk_esc}', 'Motor Jurídico Colombia 2026');"
        
        # Escapar para comando shell
        sql_shell_esc = sql.replace("'", "'\\''")
        ssh.exec_command(f"docker exec {container} psql -U postgres -c '{sql_shell_esc}'")
    
    print("✅ Carga de conocimiento finalizada.")
    ssh.close()

if __name__ == "__main__":
    insert_knowledge()
