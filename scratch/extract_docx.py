import docx
import sys

def get_docx_text(path):
    doc = docx.Document(path)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

try:
    print(get_docx_text(r"C:\Users\su-le\Downloads\Motor_Juridico_Base_Conocimiento_Legal_Colombia.docx"))
except Exception as e:
    print(f"Error: {e}")
