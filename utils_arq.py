# utils.py
import logging
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Any
import os

import pdfplumber
import pytesseract

logger = logging.getLogger(__name__)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extrai texto de bytes de um arquivo PDF, com fallback para OCR."""
    text = ""
    try:
        with BytesIO(pdf_bytes) as f, pdfplumber.open(f) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                else:
                    logger.info("Usando OCR em página de PDF (sem texto direto).")
                    try:
                        ocr_text = pytesseract.image_to_string(page.to_image(resolution=300).original, lang="por+eng")
                        if ocr_text and ocr_text.strip():
                            text += ocr_text + "\n"
                    except Exception as ocr_error:
                        logger.error(f"Erro de OCR em página de PDF: {ocr_error}")
    except Exception as e:
        logger.error(f"Erro ao processar bytes de PDF: {e}", exc_info=True)
    return text.strip()

def extract_text_from_txt_bytes(txt_bytes: bytes) -> str:
    """Extrai texto de bytes de um arquivo TXT."""
    try:
        # Tenta decodificar com UTF-8, com fallback para latin-1, comum no Brasil
        return txt_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return txt_bytes.decode('latin-1')
        except Exception as e:
            logger.error(f"Erro ao decodificar arquivo de texto: {e}")
            return ""
    except Exception as e:
        logger.error(f"Erro ao ler bytes de TXT: {e}")
        return ""

def process_uploaded_files(uploaded_files: List[Any]) -> List[Dict[str, str]]:
    """
    Processa uma lista de arquivos carregados pelo Streamlit, extraindo seu conteúdo.

    Args:
        uploaded_files: Uma lista de objetos UploadedFile do Streamlit.

    Returns:
        Lista de dicionários, cada um com 'filename' e 'content'.
    """
    documents: List[Dict[str, str]] = []
    if not uploaded_files:
        return documents

    for up_file in uploaded_files:
        if up_file is None:
            continue
        
        content = ""
        file_bytes = up_file.getvalue()
        file_name = up_file.name

        if file_name.lower().endswith(".pdf"):
            content = extract_text_from_pdf_bytes(file_bytes)
        elif file_name.lower().endswith(".txt"):
            content = extract_text_from_txt_bytes(file_bytes)
        
        if content.strip():
            documents.append({"filename": file_name, "content": content})
        else:
            logger.warning(f"Nenhum conteúdo de texto foi extraído de: {file_name}")
            
    return documents

def render_petition_template(template_path, context):
    """
    Renders a petition template with the provided context.
    :param template_path: Path to the template file
    :param context: Dictionary with keys matching placeholders in the template
    :return: Rendered string
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return template.format(**context)

# Example usage:
if __name__ == "__main__":
    context = {
        "client_name": "João Silva",
        "process_number": "12345-67.2025.8.26.0001",
        "lawyer_name": "Dr. Carlos Souza"
    }
    result = render_petition_template(
        os.path.join("petition_templates", "initial_petition_template.txt"),
        context
    )
    print(result)
