# models.py
from flask_login import UserMixin
from datetime import datetime
from app.extensions import db


class User(UserMixin):
    """
    Classe que representa um usuário para o Flask-Login.
    Herda de UserMixin para obter implementações padrão de
    propriedades como is_authenticated, is_active, etc.
    """
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.nome_completo = user_data.get('nome_completo')
        self.password_hash = user_data.get('password_hash')
        self.advogado_oab = user_data.get('advogado_oab')

    def get_id(self):
        return str(self.id)


# ---------------------------------------------------------
# 🚀 NOVO MODEL: Documento (usado apenas para tabelas do PostgreSQL)
# ---------------------------------------------------------

class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    id_processo = db.Column(
        db.String(64),
        db.ForeignKey("processos.id_processo", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Multi-tenant opcional
    tenant_id = db.Column(
        db.String(64),
        index=True,
        nullable=True
    )

    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)

    # Caminho relativo ao diretório "cases/"
    storage_path = db.Column(db.String(500), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
