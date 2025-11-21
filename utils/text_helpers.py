import datetime
import unicodedata
import re

# --- Extração e limpeza de texto ---

def extract_text(response):
    if isinstance(response, str):
        return response.strip()
    elif isinstance(response, dict):
        return response.get("text", "").strip()
    elif isinstance(response, list):
        return " ".join(str(item).strip() for item in response)
    return str(response).strip()

def clean_text(text):
    text = " ".join(text.split())
    text = unicodedata.normalize("NFKC", text)
    return text.strip()

def normalize_name(name):
    return " ".join(part.capitalize() for part in name.split())

# --- Datas em português ---

def format_date_pt(date_obj=None, formato="long"):
    meses = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    if date_obj is None:
        date_obj = datetime.datetime.now()

    if formato == "long":
        return f"{date_obj.day} de {meses[date_obj.month - 1]} de {date_obj.year}"
    elif formato == "short":
        return f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
    elif formato == "iso":
        return date_obj.strftime("%Y-%m-%d")
    else:
        raise ValueError("Formato inválido. Use 'long', 'short' ou 'iso'.")

# --- Documentos: CPF e CNPJ ---

def format_cpf(cpf: str) -> str:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def format_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

def validate_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for i in [12, 13]:
        soma = sum(int(cnpj[j]) * pesos2[j] for j in range(i))
        digito = 11 - (soma % 11)
        digito = digito if digito < 10 else 0
        if digito != int(cnpj[i]):
            return False
    return True

def detect_document_type(doc: str) -> str:
    """
    Detecta se o documento é CPF ou CNPJ com base na estrutura e validação.
    Retorna 'CPF', 'CNPJ' ou 'Inválido'.
    """
    doc = re.sub(r"\D", "", doc)

    if len(doc) == 11 and validate_cpf(doc):
        return "CPF"
    elif len(doc) == 14 and validate_cnpj(doc):
        return "CNPJ"
    else:
        return "Inválido"



# --- Valores monetários ---

def format_currency(value: float, prefix="R$") -> str:
    return f"{prefix} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_currency(text: str) -> float:
    text = re.sub(r"[^\d,\.]", "", text)
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0
