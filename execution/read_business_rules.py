import pandas as pd
import os

def read_rules():
    file_path = r"c:\Users\su-le\OneDrive\Desktop\tutelaapp\BD_Reglas_Envio_Defiendo_Colombia (1).xlsx"
    if os.path.exists(file_path):
        print(f"-- REGLAS DE NEGOCIO --")
        try:
            # Leer todas las hojas para ver cuál contiene las reglas del portal 24/7
            xl = pd.ExcelFile(file_path)
            for sheet in xl.sheet_names:
                print(f"\nSheet: {sheet}")
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(df.head(20))
        except Exception as e:
            print(f"Error reading rules: {e}")

if __name__ == "__main__":
    read_rules()
