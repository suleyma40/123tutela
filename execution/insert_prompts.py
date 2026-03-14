import json
import os
import paramiko
from dotenv import load_dotenv

def extract_prompts():
    load_dotenv()
    with open(".tmp/documentation_analysis.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    prompts_text = data['prompts']
    
    # Split by MODULE
    modules = prompts_text.split('MÓDULO')
    prompts_dict = {}
    
    for mod in modules[1:]: # Skip preamble
        lines = mod.split('\n')
        title = lines[0].strip().replace(' — ', ' ').replace(' / ', ' ')
        content = '\n'.join(lines[1:]).strip()
        prompts_dict[title] = content
        
    return prompts_dict

def insert_prompts():
    load_dotenv()
    prompts = extract_prompts()
    
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    # Create table prompts_maestros
    ssh.exec_command(f"docker exec {container} psql -U postgres -c \"CREATE TABLE IF NOT EXISTS prompts_maestros (id SERIAL PRIMARY KEY, modulo TEXT UNIQUE, prompt_text TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);\"")
    
    print(f"📥 Cargando {len(prompts)} prompts maestros...")
    
    for modulo, text in prompts.items():
        text_esc = text.replace("'", "''")
        mod_esc = modulo.replace("'", "''")
        
        sql = f"INSERT INTO prompts_maestros (modulo, prompt_text) VALUES ('{mod_esc}', '{text_esc}') ON CONFLICT (modulo) DO UPDATE SET prompt_text = EXCLUDED.prompt_text;"
        
        sql_shell_esc = sql.replace("'", "'\\''")
        ssh.exec_command(f"docker exec {container} psql -U postgres -c '{sql_shell_esc}'")
    
    print("✅ Carga de prompts finalizada.")
    ssh.close()

if __name__ == "__main__":
    insert_prompts()
