import pandas as pd
import os

def check_files():
    files = [
        "BD_Entidades_Destino_Defiendo_Colombia.xlsx",
        "BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx",
        "BD_Reglas_Envio_Defiendo_Colombia (1).xlsx"
    ]
    
    for f in files:
        full_path = os.path.join(r"c:\Users\su-le\OneDrive\Desktop\tutelaapp", f)
        if os.path.exists(full_path):
            print(f"-- Processing {f} --")
            try:
                df = pd.read_excel(full_path)
                print(f"Columns: {df.columns.tolist()}")
                print(f"First row: {df.iloc[0].to_dict() if not df.empty else 'Empty'}")
                print("-" * 30)
            except Exception as e:
                print(f"Error reading {f}: {e}")
        else:
            print(f"File not found: {f}")

if __name__ == "__main__":
    check_files()
