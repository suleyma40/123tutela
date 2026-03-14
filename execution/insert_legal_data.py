import json
import os
import paramiko
from dotenv import load_dotenv

def clean_value(val):
    if val is None or str(val).lower() == 'nan':
        return None
    return str(val).strip()

def to_bool(val):
    v = clean_value(val)
    if v is None: return False
    return v.lower() in ['si', 'yes', 'true', '1', '✓']

def insert_data():
    load_dotenv()
    with open(".tmp/documentation_analysis.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    # 1. Insert Entities from multiple sheets
    entity_sheets = ['🗺️ MAPA MAESTRO', '📧 EPS Colombia', '⚡ Empresas SP', '🏛️ Entidades Públicas']
    for sheet in entity_sheets:
        if sheet not in data['entities']: continue
        print(f"📥 Cargando Entidades de: {sheet}...")
        entities_data = data['entities'][sheet]
        
        start_idx = 0
        header_found = False
        for i, row in enumerate(entities_data):
            if any(k in str(v).upper() for v in row.values() for k in ['MÓDULO', 'ENTIDAD', 'PASO']):
                start_idx = i + 1
                header_found = True
                break
        
        if not header_found: continue

        for row in entities_data[start_idx:]:
            vals = list(row.values())
            # Ensure we have enough columns or fill with None
            while len(vals) < 10: vals.append(None)
            
            nombre_ent = clean_value(vals[2])
            if not nombre_ent: continue
            
            sql = f"""INSERT INTO entidades (modulo, paso_flujo, nombre_entidad, canal_envio, contacto_envio, genera_radicado, plazo_respuesta, observaciones, automatizable) 
            VALUES (
                '{clean_value(vals[0])}', 
                '{clean_value(vals[1])}', 
                '{nombre_ent}', 
                '{clean_value(vals[3])}', 
                '{clean_value(vals[4])}', 
                {to_bool(vals[5])}, 
                '{clean_value(vals[6])}', 
                '{clean_value(vals[7])}', 
                {to_bool(vals[8])}
            );"""
            
            sql_escaped = sql.replace("'", "'\\''")
            ssh.exec_command(f"docker exec {container} psql -U postgres -c '{sql_escaped}'")

    # 2. Insert Courts (Juzgados)
    print("📥 Cargando Juzgados...")
    if 'BASE JUZGADOS' in data['courts']:
        courts_data = data['courts']['BASE JUZGADOS']
        start_idx = 0
        for i, row in enumerate(courts_data):
            if any('DEPARTAMENTO' in str(v).upper() for v in row.values()):
                start_idx = i + 1
                break
                
        for row in courts_data[start_idx:]:
            vals = list(row.values())
            while len(vals) < 13: vals.append(None)
            
            correo = clean_value(vals[4])
            if not correo: continue
            
            sql = f"""INSERT INTO juzgados (departamento, municipio, tipo_oficina, correo_reparto, correo_alternativo, tipo_tutela, asunto_recomendado, plataforma_oficial, url_referencia, codigo_interno, prioridad, notas) 
            VALUES (
                '{clean_value(vals[1])}', 
                '{clean_value(vals[2])}', 
                '{clean_value(vals[3])}', 
                '{correo}', 
                '{clean_value(vals[5])}', 
                '{clean_value(vals[6])}', 
                '{clean_value(vals[7])}', 
                '{clean_value(vals[8])}', 
                '{clean_value(vals[9])}', 
                '{clean_value(vals[10])}', 
                '{clean_value(vals[11])}', 
                '{clean_value(vals[12])}'
            );"""
            
            sql_escaped = sql.replace("'", "'\\''")
            ssh.exec_command(f"docker exec {container} psql -U postgres -c '{sql_escaped}'")
    
    print("✅ Carga finalizada.")
    ssh.close()

if __name__ == "__main__":
    insert_data()
