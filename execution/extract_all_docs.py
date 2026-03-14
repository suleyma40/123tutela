import os
import pandas as pd
from docx import Document
import json

def extract_docx(path):
    if not os.path.exists(path):
        return f"File not found: {path}"
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_xlsx(path):
    if not os.path.exists(path):
        return f"File not found: {path}"
    # Read all sheets
    xls = pd.ExcelFile(path)
    output = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        output[sheet_name] = df.to_dict(orient='records')
    return output

def main():
    downloads = r"c:\Users\su-le\Downloads"
    files = {
        "business_plan": "Plan_Negocios_Defiendo_Colombia.docx",
        "prompts": "Prompts_Maestros_IA_Defiendo_Colombia.docx",
        "legal_base": "Motor_Juridico_Base_Conocimiento_Legal_Colombia.docx",
        "entities": "BD_Entidades_Destino_Defiendo_Colombia.xlsx",
        "courts": "BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx",
        "rules": "BD_Reglas_Envio_Defiendo_Colombia.xlsx"
    }
    
    analysis = {}
    
    print("Reading docx files...")
    for key in ["business_plan", "prompts", "legal_base"]:
        analysis[key] = extract_docx(os.path.join(downloads, files[key]))
    
    print("Reading xlsx files...")
    for key in ["entities", "courts", "rules"]:
        analysis[key] = extract_xlsx(os.path.join(downloads, files[key]))
    
    os.makedirs(".tmp", exist_ok=True)
    with open(".tmp/documentation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # Save a human readable summary too
    with open(".tmp/documentation_summary.txt", "w", encoding="utf-8") as f:
        f.write("=== BUSINESS PLAN ===\n")
        f.write(analysis["business_plan"][:2000] + "...\n\n")
        f.write("=== PROMPTS ===\n")
        f.write(analysis["prompts"][:2000] + "...\n\n")
        f.write("=== LEGAL BASE ===\n")
        f.write(analysis["legal_base"][:2000] + "...\n\n")
        f.write("=== DATA PREVIEW ===\n")
        for key in ["entities", "courts", "rules"]:
            f.write(f"--- {key} ---\n")
            sheet0 = list(analysis[key].keys())[0]
            preview = analysis[key][sheet0][:5]
            f.write(json.dumps(preview, indent=2) + "\n\n")

if __name__ == "__main__":
    main()
