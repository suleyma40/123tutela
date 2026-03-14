import pandas as pd
import os
import paramiko
from dotenv import load_dotenv

def clean_value(val):
    if pd.isna(val) or str(val).lower() == 'nan':
        return None
    # Limpiar saltos de línea y comillas
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
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    
    container = "bw7aj85ekz1p65w04lptq93j"
    
    def execute_sql(sql):
        try:
            # Escapar comillas dobles externas para shell
            cmd = f"docker exec {container} psql -U postgres -c \"{sql}\""
            ssh.exec_command(cmd)
        except:
            pass

    # 1. Cargar Entidades
    print("📥 Cargando Entidades...")
    sheets = ['🗺️ MAPA MAESTRO', '📧 EPS Colombia', '⚡ Empresas SP', '🏛️ Entidades Públicas']
    for sheet in sheets:
        try:
            df = pd.read_excel(entidades_file, sheet_name=sheet)
            if df.empty: continue
            
            # Cambiar nombres de columnas para facilitar acceso por índice
            df.columns = range(len(df.columns))
            
            # Buscar fila de cabecera
            start_row = 0
            for i, row in df.iterrows():
                # Si alguna celda contiene "ENTIDAD" o "MÓDULO"
                if any(str(v).upper() in ['MÓDULO', 'ENTIDAD', 'CONCEPTO'] for v in row.values):
                    start_row = i + 1
                    break
            
            for _, row in df.iloc[start_row:].iterrows():
                # Validar que al menos la columna "Entidad" (asumimos índice 2) tenga datos
                if len(row) < 3 or pd.isna(row[2]): continue
                
                # Mapeo conservador: 0: Modulo, 1: Paso, 2: Nombre, 3: Canal, 4: Contacto, 5: Radicado, 6: Plazo, 7: Obs, 8: Auto
                # Ajustar si sobran o faltan
                sql = f"""
                INSERT INTO entidades (modulo, paso_flujo, nombre_entidad, canal_envio, contacto_envio, genera_radicado, plazo_respuesta, observaciones, automatizable)
                VALUES (
                    '{clean_value(row[0]) if len(row) > 0 else ''}', 
                    '{clean_value(row[1]) if len(row) > 1 else ''}', 
                    '{clean_value(row[2])}', 
                    '{clean_value(row[3]) if len(row) > 3 else ''}', 
                    '{clean_value(row[4]) if len(row) > 4 else ''}', 
                    {to_bool(row[5]) if len(row) > 5 else 'FALSE'}, 
                    '{clean_value(row[6]) if len(row) > 6 else ''}', 
                    '{clean_value(row[7]) if len(row) > 7 else ''}', 
                    {to_bool(row[8]) if len(row) > 8 else 'TRUE'}
                ) ON CONFLICT DO NOTHING;"""
                execute_sql(sql)
        except Exception as e:
            print(f"Error in sheet {sheet}: {e}")

    # 2. Cargar Juzgados
    print("📥 Cargando Juzgados...")
    try:
        df_j = pd.read_excel(juzgados_file, sheet_name='BASE JUZGADOS')
        df_j.columns = range(len(df_j.columns))
        
        start_row = 0
        for i, row in df_j.iterrows():
            if any(str(v).upper() in ['DEPARTAMENTO', 'MUNICIPIO'] for v in row.values):
                start_row = i + 1
                break
        
        for _, row in df_j.iloc[start_row:].iterrows():
            # Validar columna de correo (asumimos índice 4)
            if len(row) < 5 or pd.isna(row[4]): continue
            
            sql = f"""
            INSERT INTO juzgados (departamento, municipio, tipo_oficina, correo_reparto, correo_alternativo, tipo_tutela, asunto_recomendado, plataforma_oficial, url_referencia, codigo_interno, prioridad, notas)
            VALUES (
                '{clean_value(row[1]) if len(row) > 1 else ''}', 
                '{clean_value(row[2]) if len(row) > 2 else ''}', 
                '{clean_value(row[3]) if len(row) > 3 else ''}', 
                '{clean_value(row[4])}', 
                '{clean_value(row[5]) if len(row) > 5 else ''}', 
                '{clean_value(row[6]) if len(row) > 6 else ''}', 
                '{clean_value(row[7]) if len(row) > 7 else ''}', 
                '{clean_value(row[8]) if len(row) > 8 else ''}', 
                '{clean_value(row[9]) if len(row) > 9 else ''}', 
                '{clean_value(row[10]) if len(row) > 10 else ''}', 
                '{clean_value(row[11]) if len(row) > 11 else ''}', 
                '{clean_value(row[12]) if len(row) > 12 else ''}'
            ) ON CONFLICT (codigo_interno) DO UPDATE SET correo_reparto = EXCLUDED.correo_reparto;"""
            execute_sql(sql)
    except Exception as e:
        print(f"Error loading juzgados: {e}")

    print("✅ Sincronización completada con manejo de robustez.")
    ssh.close()

if __name__ == "__main__":
    sync_data()
