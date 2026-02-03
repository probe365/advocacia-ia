"""convert core id columns to text

Revision ID: 20260124_convert_ids_to_text
Revises: 20260124_repair_core_tables
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260124_convert_ids_to_text"
down_revision: Union[str, None] = "20260124_repair_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STRING_LEN = 64


def _get_column(inspector, table: str, column: str):
    for col in inspector.get_columns(table):
        if col["name"] == column:
            return col
    return None


def _is_string_type(col_type) -> bool:
    return isinstance(col_type, (sa.String, sa.Text))


def _drop_fk_if_exists(inspector, table: str, referred_table: str) -> None:
    for fk in inspector.get_foreign_keys(table):
        if fk.get("referred_table") == referred_table:
            name = fk.get("name")
            if name:
                op.drop_constraint(name, table, type_="foreignkey")


def _has_column(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _ensure_fk(inspector, name: str, source: str, referent: str, local_cols, remote_cols, ondelete: str) -> None:
    for fk in inspector.get_foreign_keys(source):
        if fk.get("referred_table") == referent and fk.get("constrained_columns") == local_cols:
            return
    op.create_foreign_key(name, source, referent, local_cols, remote_cols, ondelete=ondelete)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # clientes.id_cliente
    if inspector.has_table("clientes"):
        col = _get_column(inspector, "clientes", "id_cliente")
        if col and not _is_string_type(col["type"]):
            with op.batch_alter_table("clientes") as batch:
                batch.alter_column(
                    "id_cliente",
                    existing_type=col["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=False,
                    postgresql_using="id_cliente::text",
                )

    # processos.id_processo + processos.id_cliente
    if inspector.has_table("processos"):
        _drop_fk_if_exists(inspector, "processos", "clientes")
        _drop_fk_if_exists(inspector, "processos", "advogados")

        col_proc = _get_column(inspector, "processos", "id_processo")
        col_cli = _get_column(inspector, "processos", "id_cliente")
        with op.batch_alter_table("processos") as batch:
            if col_proc and not _is_string_type(col_proc["type"]):
                batch.alter_column(
                    "id_processo",
                    existing_type=col_proc["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=False,
                    postgresql_using="id_processo::text",
                )
            if col_cli and not _is_string_type(col_cli["type"]):
                batch.alter_column(
                    "id_cliente",
                    existing_type=col_cli["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=True,
                    postgresql_using="id_cliente::text",
                )

        inspector = sa.inspect(bind)
        _ensure_fk(inspector, "processos_id_cliente_fkey", "processos", "clientes", ["id_cliente"], ["id_cliente"], "CASCADE")
        _ensure_fk(inspector, "processos_advogado_oab_fkey", "processos", "advogados", ["advogado_oab"], ["oab"], "SET NULL")

    # chat_turns.id_processo
    if inspector.has_table("chat_turns"):
        _drop_fk_if_exists(inspector, "chat_turns", "processos")
        col = _get_column(inspector, "chat_turns", "id_processo")
        if col and not _is_string_type(col["type"]):
            with op.batch_alter_table("chat_turns") as batch:
                batch.alter_column(
                    "id_processo",
                    existing_type=col["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=False,
                    postgresql_using="id_processo::text",
                )
        inspector = sa.inspect(bind)
        if _has_column(inspector, "chat_turns", "id_processo") and _has_column(inspector, "processos", "id_processo"):
            _ensure_fk(inspector, "fk_chat_turns_processo", "chat_turns", "processos", ["id_processo"], ["id_processo"], "CASCADE")
        elif _has_column(inspector, "chat_turns", "process_id") and _has_column(inspector, "processos", "process_id"):
            _ensure_fk(inspector, "fk_chat_turns_processo", "chat_turns", "processos", ["process_id"], ["process_id"], "CASCADE")

    # partes_adversas.id_processo
    if inspector.has_table("partes_adversas"):
        _drop_fk_if_exists(inspector, "partes_adversas", "processos")
        col = _get_column(inspector, "partes_adversas", "id_processo")
        if col and not _is_string_type(col["type"]):
            with op.batch_alter_table("partes_adversas") as batch:
                batch.alter_column(
                    "id_processo",
                    existing_type=col["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=False,
                    postgresql_using="id_processo::text",
                )
        inspector = sa.inspect(bind)
        if _has_column(inspector, "partes_adversas", "id_processo") and _has_column(inspector, "processos", "id_processo"):
            _ensure_fk(inspector, "fk_partes_adversas_processo", "partes_adversas", "processos", ["id_processo"], ["id_processo"], "CASCADE")
        elif _has_column(inspector, "partes_adversas", "process_id") and _has_column(inspector, "processos", "process_id"):
            _ensure_fk(inspector, "fk_partes_adversas_processo", "partes_adversas", "processos", ["process_id"], ["process_id"], "CASCADE")

    # documentos.id_processo / documentos.id_cliente
    if inspector.has_table("documentos"):
        _drop_fk_if_exists(inspector, "documentos", "processos")
        _drop_fk_if_exists(inspector, "documentos", "clientes")
        col_proc = _get_column(inspector, "documentos", "id_processo")
        col_cli = _get_column(inspector, "documentos", "id_cliente")
        with op.batch_alter_table("documentos") as batch:
            if col_proc and not _is_string_type(col_proc["type"]):
                batch.alter_column(
                    "id_processo",
                    existing_type=col_proc["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=False,
                    postgresql_using="id_processo::text",
                )
            if col_cli and not _is_string_type(col_cli["type"]):
                batch.alter_column(
                    "id_cliente",
                    existing_type=col_cli["type"],
                    type_=sa.String(length=STRING_LEN),
                    existing_nullable=True,
                    postgresql_using="id_cliente::text",
                )

        inspector = sa.inspect(bind)
        if _has_column(inspector, "documentos", "id_processo") and _has_column(inspector, "processos", "id_processo"):
            _ensure_fk(inspector, "fk_documentos_processos", "documentos", "processos", ["id_processo"], ["id_processo"], "CASCADE")
        elif _has_column(inspector, "documentos", "process_id") and _has_column(inspector, "processos", "process_id"):
            _ensure_fk(inspector, "fk_documentos_processos", "documentos", "processos", ["process_id"], ["process_id"], "CASCADE")
        _ensure_fk(inspector, "fk_documentos_clientes", "documentos", "clientes", ["id_cliente"], ["id_cliente"], "NO ACTION")


def downgrade() -> None:
    # Non-destructive: avoid converting string ids back to integers.
    pass
