"""repair core tables for SaaS multi-tenant

Revision ID: 20260124_repair_core_tables
Revises: 20260124_fix_pp_role
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260124_repair_core_tables"
down_revision: Union[str, None] = "20260124_fix_pp_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _ensure_documento_columns(inspector) -> None:
    if not inspector.has_table("documentos"):
        op.create_table(
            "documentos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.String(length=50), nullable=False),
            sa.Column("id_cliente", sa.String(length=64), nullable=True),
            sa.Column("id_processo", sa.String(length=64), nullable=False),
            sa.Column("tipo", sa.String(length=20), nullable=False),
            sa.Column("titulo", sa.String(length=255), nullable=False),
            sa.Column("descricao", sa.Text(), nullable=True),
            sa.Column("arquivo_nome", sa.String(length=255), nullable=False),
            sa.Column("mime_type", sa.String(length=100), nullable=True),
            sa.Column("tamanho_bytes", sa.BigInteger(), nullable=True),
            sa.Column("storage_backend", sa.String(length=50), nullable=False, server_default=sa.text("'local'")),
            sa.Column("storage_path", sa.String(length=500), nullable=False),
            sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
            sa.Column("criado_por_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_documentos_id_processo", "documentos", ["id_processo"])
        op.create_index("ix_documentos_tenant_id", "documentos", ["tenant_id"])
        return

    with op.batch_alter_table("documentos") as batch:
        if not _has_column(inspector, "documentos", "tenant_id"):
            batch.add_column(sa.Column("tenant_id", sa.String(length=50), nullable=True))
        if not _has_column(inspector, "documentos", "id_cliente"):
            batch.add_column(sa.Column("id_cliente", sa.String(length=64), nullable=True))
        if not _has_column(inspector, "documentos", "id_processo"):
            batch.add_column(sa.Column("id_processo", sa.String(length=64), nullable=True))
        if not _has_column(inspector, "documentos", "tipo"):
            batch.add_column(sa.Column("tipo", sa.String(length=20), nullable=True))
        if not _has_column(inspector, "documentos", "titulo"):
            batch.add_column(sa.Column("titulo", sa.String(length=255), nullable=True))
        if not _has_column(inspector, "documentos", "descricao"):
            batch.add_column(sa.Column("descricao", sa.Text(), nullable=True))
        if not _has_column(inspector, "documentos", "arquivo_nome"):
            batch.add_column(sa.Column("arquivo_nome", sa.String(length=255), nullable=True))
        if not _has_column(inspector, "documentos", "mime_type"):
            batch.add_column(sa.Column("mime_type", sa.String(length=100), nullable=True))
        if not _has_column(inspector, "documentos", "tamanho_bytes"):
            batch.add_column(sa.Column("tamanho_bytes", sa.BigInteger(), nullable=True))
        if not _has_column(inspector, "documentos", "storage_backend"):
            batch.add_column(sa.Column("storage_backend", sa.String(length=50), nullable=True))
        if not _has_column(inspector, "documentos", "storage_path"):
            batch.add_column(sa.Column("storage_path", sa.String(length=500), nullable=True))
        if not _has_column(inspector, "documentos", "checksum_sha256"):
            batch.add_column(sa.Column("checksum_sha256", sa.String(length=64), nullable=True))
        if not _has_column(inspector, "documentos", "criado_por_id"):
            batch.add_column(sa.Column("criado_por_id", sa.Integer(), nullable=True))
        if not _has_column(inspector, "documentos", "created_at"):
            batch.add_column(sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True))
        if not _has_column(inspector, "documentos", "updated_at"):
            batch.add_column(sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True))

    op.execute("UPDATE documentos SET tenant_id = COALESCE(tenant_id, 'public')")


def _ensure_chat_turns(inspector) -> None:
    if inspector.has_table("chat_turns"):
        if not _has_column(inspector, "chat_turns", "tenant_id"):
            with op.batch_alter_table("chat_turns") as batch:
                batch.add_column(sa.Column("tenant_id", sa.String(length=50), nullable=True))
        return

    op.create_table(
        "chat_turns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_processo", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_chat_turns_processo", "chat_turns", ["id_processo"])
    op.create_index("ix_chat_turns_tenant", "chat_turns", ["tenant_id"])


def _ensure_partes_adversas(inspector) -> None:
    if inspector.has_table("partes_adversas"):
        if not _has_column(inspector, "partes_adversas", "tenant_id"):
            with op.batch_alter_table("partes_adversas") as batch:
                batch.add_column(sa.Column("tenant_id", sa.String(length=50), nullable=True))
        return

    op.create_table(
        "partes_adversas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_processo", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=50), nullable=False),
        sa.Column("tipo_parte", sa.String(length=20), nullable=False),
        sa.Column("nome_completo", sa.String(length=255), nullable=False),
        sa.Column("cpf_cnpj", sa.String(length=18), nullable=True),
        sa.Column("rg", sa.String(length=20), nullable=True),
        sa.Column("qualificacao", sa.Text(), nullable=True),
        sa.Column("endereco_completo", sa.Text(), nullable=True),
        sa.Column("bairro", sa.String(length=100), nullable=True),
        sa.Column("cidade", sa.String(length=100), nullable=True),
        sa.Column("estado", sa.String(length=2), nullable=True),
        sa.Column("cep", sa.String(length=9), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("advogado_nome", sa.String(length=255), nullable=True),
        sa.Column("advogado_oab", sa.String(length=20), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_partes_adversas_processo", "partes_adversas", ["id_processo"])
    op.create_index("idx_partes_adversas_tenant", "partes_adversas", ["tenant_id"])
    op.create_index("idx_partes_adversas_cpf_cnpj", "partes_adversas", ["cpf_cnpj"])
    op.create_index("idx_partes_adversas_nome", "partes_adversas", ["nome_completo"])
    op.create_index("idx_partes_adversas_tipo", "partes_adversas", ["tipo_parte"])
    op.create_index("idx_partes_adversas_tenant_processo", "partes_adversas", ["tenant_id", "id_processo"])


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _ensure_documento_columns(inspector)
    _ensure_chat_turns(inspector)
    _ensure_partes_adversas(inspector)


def downgrade() -> None:
    # No destructive downgrades for repair migration.
    pass
