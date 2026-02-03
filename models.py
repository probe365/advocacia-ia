# models.py
from flask_login import UserMixin
from datetime import datetime
from typing import Any, cast
from app.extensions import db as _db

from sqlalchemy.dialects.postgresql import JSONB, UUID
from flask_sqlalchemy import SQLAlchemy


db: Any = cast(Any, _db)


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
        self.tenant_id = user_data.get('tenant_id')

    def get_id(self):
        return str(self.id)


# ---------------------------------------------------------
# 🚀 NOVO MODEL: Escritorio (tabela de escritorio do PostgreSQL)
# ---------------------------------------------------------

class Escritorio(db.Model):
    __tablename__ = "escritorio"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255))
    tenant_id = db.Column(db.String(64), unique=True, nullable=False)
# 🚀 NOVO MODEL: Clientes (tabela de clientes do PostgreSQL)
# ---------------------------------------------------------

class Clientes(db.Model):
    __tablename__ = "clientes"
    id_cliente = db.Column(db.String(64), primary_key=True)
    tipo_pessoa = db.Column(db.String(50))
    nome_completo = db.Column(db.String(255))
    cpf_cnpj = db.Column(db.String(32))
    rg_ie = db.Column(db.String(32))
    nacionalidade = db.Column(db.String(64))
    estado_civil = db.Column(db.String(32))
    profissao = db.Column(db.String(64))
    endereco_completo = db.Column(db.String(255))
    telefone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    responsavel_pj = db.Column(db.String(255))
    data_cadastro = db.Column(db.DateTime)
    observacoes = db.Column(db.Text)
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
# 🚀 NOVO MODEL: Usuarios (tabela de usuarios do PostgreSQL)
# ---------------------------------------------------------

class Usuarios(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(255))
    advogado_oab = db.Column(db.String(32))
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
# 🚀 NOVO MODEL: Processos (tabela de processos do PostgreSQL)
# ---------------------------------------------------------

class Processos(db.Model):
    __tablename__ = "processos"

    id_processo = db.Column(db.String(64), primary_key=True)
    id_cliente = db.Column(db.String(64), index=True)
    nome_caso = db.Column(db.String(255))
    numero_cnj = db.Column(db.String(64))
    status = db.Column(db.String(50))
    data_inicio = db.Column(db.DateTime)
    advogado_oab = db.Column(db.String(32))
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
    tipo_parte = db.Column(db.String(64))
    local_tramite = db.Column(db.String(128))
    comarca = db.Column(db.String(128))
    area_atuacao = db.Column(db.String(128))
    instancia = db.Column(db.String(64))
    subfase = db.Column(db.String(64))
    assunto = db.Column(db.String(128))
    valor_causa = db.Column(db.Numeric)
    data_distribuicao = db.Column(db.DateTime)
    data_encerramento = db.Column(db.DateTime)
    sentenca = db.Column(db.Text)
    em_execucao = db.Column(db.Boolean, default=False)
    segredo_justica = db.Column(db.Boolean, default=False)
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
        nullable=False,
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
# ---------------------------------------------------------
# 🚀 NOVO MODEL: Model for Petitions Table
# ---------------------------------------------------------

class Petition(db.Model):
    __tablename__ = 'petitions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cliente_id = db.Column(db.String(64), db.ForeignKey('clientes.id_cliente'))
    process_id = db.Column(db.String(64), db.ForeignKey('processos.id_processo'))
    petition_type = db.Column(db.String(100), nullable=False)
    content = db.Column(JSONB)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


# ---------------------------------------------------------
# 🚀 NOVOS MODELS: DJE Push e Andamentos
# ---------------------------------------------------------

class DjePushSubscription(db.Model):
    __tablename__ = "dje_push_subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
    process_id = db.Column(db.String(64), index=True, nullable=False)
    cnj_number = db.Column(db.String(64), nullable=False)
    external_id = db.Column(db.String(128))
    webhook_url = db.Column(db.String(500))
    enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(64))
    last_sync_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class DjePushEvent(db.Model):
    __tablename__ = "dje_push_events"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
    process_id = db.Column(db.String(64), index=True, nullable=False)
    cnj_number = db.Column(db.String(64), nullable=False)
    event_type = db.Column(db.String(64))
    event_title = db.Column(db.String(255))
    event_date = db.Column(db.DateTime)
    prazo_final = db.Column(db.DateTime)
    status_ciencia = db.Column(db.String(64))
    external_id = db.Column(db.String(128))
    payload = db.Column(JSONB)
    event_hash = db.Column(db.String(64), nullable=False)
    origem = db.Column(db.String(64), default="djecnj")
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DjeAndamento(db.Model):
    __tablename__ = "dje_andamentos"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
    process_id = db.Column(db.String(64), index=True, nullable=False)
    cnj_number = db.Column(db.String(64), nullable=False)
    movimento_data = db.Column(db.DateTime)
    descricao = db.Column(db.String(500))
    tipo_comunicacao = db.Column(db.String(64))
    tribunal = db.Column(db.String(64))
    orgao = db.Column(db.String(128))
    grau = db.Column(db.String(64))
    external_id = db.Column(db.String(128))
    payload = db.Column(JSONB)
    event_hash = db.Column(db.String(64), nullable=False)
    origem = db.Column(db.String(64), default="djecnj")
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DjeEmailMessage(db.Model):
    __tablename__ = "dje_email_messages"
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = db.Column(db.String(64), index=True, nullable=False)
    process_number = db.Column(db.String(64))
    source = db.Column(db.String(64))
    movement_at = db.Column(db.DateTime)
    subject = db.Column(db.Text)
    body_text = db.Column(db.Text)
    body_html = db.Column(db.Text)
    message_id = db.Column(db.String(255))
    dedupe_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DjeInboxState(db.Model):
    __tablename__ = "dje_inbox_state"
    tenant_id = db.Column(db.String(64), primary_key=True)
    mailbox = db.Column(db.String(255), primary_key=True)
    last_uid = db.Column(db.BigInteger)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())