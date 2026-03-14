import pandas as pd
import os
import paramiko
from dotenv import load_dotenv
import sys

def clean_value(val):
    if pd.isna(val) or str(val).lower() == 'nan':
        return None
    return str(val).strip().replace("\n", " ").replace("'", "''")

def to_bool(val):
    v = str(val).lower()
    if any(k in v for k in ['si', 'yes', 'true', '1', '✓']):
        return 'TRUE'
    return 'FALSE'

def sync_data():
    load_dotenv()
    
    entidades_file = r"c:\Users\su-le\OneDrive\Desktop\tutelaapp\BD_Entidades_Destino_Defiendo_Colombia.xlsx"
    juzgados_file = r"c:\Users\su-le\OneDrive\Desktop\tutelaapp\BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx"
    
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    container = "bw7aj85ekz1p65w04lptq93j"
    
    print(f"🔗 Conectando a {ip} via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=user, password=password)
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    def execute_sql(sql):
        cmd = f"docker exec {container} psql -U postgres -d 123tutela -c \"{sql}\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        err = stderr.read().decode().strip()
        if err:
            if "already exists" not in err and "duplicate key" not in err:
                print(f"⚠️ SQL Error: {err}")
        return stdout.read().decode().strip()

    # 1. Cargar Entidades
    print("📥 Cargando Entidades...")
    sheets = ['🗺️ MAPA MAESTRO', '📧 EPS Colombia', '⚡ Empresas SP', '🏛️ Entidades Públicas']
    total_entidades = 0
    for sheet in sheets:
        try:
            df = pd.read_excel(entidades_file, sheet_name=sheet)
            if df.empty: continue
            df.columns = range(len(df.columns))
            
            start_row = 0
            for i, row in df.iterrows():
                if any(str(v).upper() in ['MÓDULO', 'ENTIDAD', 'CONCEPTO'] for v in row.values):
                    start_row = i + 1
                    break
            
            for _, row in df.iloc[start_row:].iterrows():
                if len(row) < 3 or pd.isna(row[2]): continue
                sql = f"INSERT INTO entidades (modulo, paso_flujo, nombre_entidad, canal_envio, contacto_envio, genera_radicado, plazo_respuesta, observaciones, automatizable) VALUES ('{clean_value(row[0])}', '{clean_value(row[1])}', '{clean_value(row[2])}', '{clean_value(row[3])}', '{clean_value(row[4])}', {to_bool(row[5])}, '{clean_value(row[6])}', '{clean_value(row[7])}', {to_bool(row[8])}) ON CONFLICT DO NOTHING;"
                execute_sql(sql)
                total_entidades += 1
        except Exception as e:
            print(f"❌ Error en hoja {sheet}: {e}")

    # 2. Cargar Juzgados
    print("📥 Cargando Juzgados...")
    total_juzgados = 0
    try:
        df_j = pd.read_excel(juzgados_file, sheet_name='BASE JUZGADOS')
        df_j.columns = range(len(df_j.columns))
        
        start_row = 0
        for i, row in df_j.iterrows():
            if any(str(v).upper() in ['DEPARTAMENTO', 'MUNICIPIO'] for v in row.values):
                start_row = i + 1
                break
        
        for _, row in df_j.iloc[start_row:].iterrows():
            if len(row) < 5 or pd.isna(row[4]): continue
            sql = f"INSERT INTO juzgados (departamento, municipio, tipo_oficina, correo_reparto, correo_alternativo, tipo_tutela, asunto_recomendado, plataforma_oficial, url_referencia, codigo_interno, prioridad, notas) VALUES ('{clean_value(row[1])}', '{clean_value(row[2])}', '{clean_value(row[3])}', '{clean_value(row[4])}', '{clean_value(row[5])}', '{clean_value(row[6])}', '{clean_value(row[7])}', '{clean_value(row[8])}', '{clean_value(row[9])}', '{clean_value(row[10])}', '{clean_value(row[11])}', '{clean_value(row[12])}') ON CONFLICT (codigo_interno) DO UPDATE SET correo_reparto = EXCLUDED.correo_reparto;"
            execute_sql(sql)
            total_juzgados += 1
    except Exception as e:
        print(f"❌ Error cargando juzgados: {e}")

    print(f"✅ Sincronización Finalizada. Entidades: {total_entidades}, Juzgados: {total_juzgados}")
    ssh.close()

if __name__ == "__main__":
    sync_data()
