import pandas as pd
import os
import paramiko
from dotenv import load_dotenv

def clean_value(val):
    if pd.isna(val) or str(val).lower() == 'nan':
        return None
    return str(val).strip().replace("'", "''")

def to_bool(val):
    v = str(val).lower()
    if v in ['si', 'yes', 'true', '1', '✓']:
        return 'TRUE'
    return 'FALSE'

def sync_data():
    load_dotenv()
    
    # Archivos
    entidades_file = r"c:\Users\su-le\OneDrive\Desktop\tutelaapp\BD_Entidades_Destino_Defiendo_Colombia.xlsx"
    juzgados_file = r"c:\Users\su-le\OneDrive\Desktop\tutelaapp\BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx"
    
    # Credenciales VPS
    ip = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    # Suponiendo que el contenedor de la DB es el mismo (bw7aj85ekz1p65w04lptq93j)
    container = "bw7aj85ekz1p65w04lptq93j"
    
    def execute_sql(sql):
        try:
            # Escapar comillas dobles para el shell y ejecutar
            cmd = f"docker exec {container} psql -U postgres -c \"{sql}\""
            stdin, stdout, stderr = ssh.exec_command(cmd)
            err = stderr.read().decode()
            if err:
                # print(f"SQL Error: {err}")
                pass
        except Exception as e:
            # print(f"Execution failed: {e}")
            pass

    # 1. Cargar Entidades
    print("📥 Cargando Entidades...")
    sheets = ['🗺️ MAPA MAESTRO', '📧 EPS Colombia', '⚡ Empresas SP', '🏛️ Entidades Públicas']
    for sheet in sheets:
        try:
            df = pd.read_excel(entidades_file, sheet_name=sheet)
            # Detectar cabecera (Módulo / Entidad)
            start_row = 0
            for i, row in df.iterrows():
                if any(str(v).upper() in ['MÓDULO', 'ENTIDAD'] for v in row.values):
                    start_row = i + 1
                    break
            
            for _, row in df.iloc[start_row:].iterrows():
                vals = row.values
                if len(vals) < 3 or pd.isna(vals[2]): continue
                
                sql = f"""
                INSERT INTO entidades (modulo, paso_flujo, nombre_entidad, canal_envio, contacto_envio, genera_radicado, plazo_respuesta, observaciones, automatizable)
                VALUES (
                    '{clean_value(vals[0])}', 
                    '{clean_value(vals[1])}', 
                    '{clean_value(vals[2])}', 
                    '{clean_value(vals[3])}', 
                    '{clean_value(vals[4])}', 
                    {to_bool(vals[5])}, 
                    '{clean_value(vals[6])}', 
                    '{clean_value(vals[7])}', 
                    {to_bool(vals[8])}
                ) ON CONFLICT DO NOTHING;"""
                execute_sql(sql)
        except Exception as e:
            print(f"Error in sheet {sheet}: {e}")

    # 2. Cargar Juzgados
    print("📥 Cargando Juzgados...")
    try:
        df_j = pd.read_excel(juzgados_file, sheet_name='BASE JUZGADOS')
        # Detectar cabecera (Departamento / Correo)
        start_row = 0
        for i, row in df_j.iterrows():
            if any(str(v).upper() in ['DEPARTAMENTO', 'MUNICIPIO', 'CORREO'] for v in row.values):
                start_row = i + 1
                break
        
        for _, row in df_j.iloc[start_row:].iterrows():
            vals = row.values
            if len(vals) < 5 or pd.isna(vals[4]): continue
            
            sql = f"""
            INSERT INTO juzgados (departamento, municipio, tipo_oficina, correo_reparto, correo_alternativo, tipo_tutela, asunto_recomendado, plataforma_oficial, url_referencia, codigo_interno, prioridad, notas)
            VALUES (
                '{clean_value(vals[1])}', 
                '{clean_value(vals[2])}', 
                '{clean_value(vals[3])}', 
                '{clean_value(vals[4])}', 
                '{clean_value(vals[5])}', 
                '{clean_value(vals[6])}', 
                '{clean_value(vals[7])}', 
                '{clean_value(vals[8])}', 
                '{clean_value(vals[9])}', 
                '{clean_value(vals[10])}', 
                '{clean_value(vals[11])}', 
                '{clean_value(vals[12])}'
            ) ON CONFLICT (codigo_interno) DO UPDATE SET correo_reparto = EXCLUDED.correo_reparto;"""
            execute_sql(sql)
    except Exception as e:
        print(f"Error loading juzgados: {e}")

    print("✅ Sincronización completada.")
    ssh.close()

if __name__ == "__main__":
    sync_data()
