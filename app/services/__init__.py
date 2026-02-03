# app/services/__init__.py

import app
from .petition_service import PetitionService
from .cadastro_service import CadastroService
from .export_service import ExportService



__all__ = [
    "PetitionService",
    "CadastroService",
    "ExportService",
]
