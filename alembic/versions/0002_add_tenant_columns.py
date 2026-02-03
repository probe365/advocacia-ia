"""Add tenant_id columns

Revision ID: 0002_add_tenant_columns
Revises: 0001_create_core_tables
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_tenant_columns'
down_revision = '0001_create_core_tables'
branch_labels = None
depends_on = None

def _has_column(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _has_index(inspector, table: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table))


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table("clientes"):
        with op.batch_alter_table("clientes", schema=None) as batch:
            if not _has_column(inspector, "clientes", "tenant_id"):
                batch.add_column(sa.Column("tenant_id", sa.String(), nullable=True))
        if not _has_index(inspector, "clientes", "ix_clientes_tenant_id"):
            op.create_index("ix_clientes_tenant_id", "clientes", ["tenant_id"])

    if inspector.has_table("processos"):
        with op.batch_alter_table("processos", schema=None) as batch:
            if not _has_column(inspector, "processos", "tenant_id"):
                batch.add_column(sa.Column("tenant_id", sa.String(), nullable=True))
        if not _has_index(inspector, "processos", "ix_processos_tenant_id"):
            op.create_index("ix_processos_tenant_id", "processos", ["tenant_id"])

    if inspector.has_table("usuarios"):
        with op.batch_alter_table("usuarios", schema=None) as batch:
            if not _has_column(inspector, "usuarios", "tenant_id"):
                batch.add_column(sa.Column("tenant_id", sa.String(), nullable=True))
        if not _has_index(inspector, "usuarios", "ix_usuarios_tenant_id"):
            op.create_index("ix_usuarios_tenant_id", "usuarios", ["tenant_id"])


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table("usuarios"):
        if _has_index(inspector, "usuarios", "ix_usuarios_tenant_id"):
            op.drop_index("ix_usuarios_tenant_id", table_name="usuarios")
        if _has_column(inspector, "usuarios", "tenant_id"):
            with op.batch_alter_table("usuarios", schema=None) as batch:
                batch.drop_column("tenant_id")

    if inspector.has_table("processos"):
        if _has_index(inspector, "processos", "ix_processos_tenant_id"):
            op.drop_index("ix_processos_tenant_id", table_name="processos")
        if _has_column(inspector, "processos", "tenant_id"):
            with op.batch_alter_table("processos", schema=None) as batch:
                batch.drop_column("tenant_id")

    if inspector.has_table("clientes"):
        if _has_index(inspector, "clientes", "ix_clientes_tenant_id"):
            op.drop_index("ix_clientes_tenant_id", table_name="clientes")
        if _has_column(inspector, "clientes", "tenant_id"):
            with op.batch_alter_table("clientes", schema=None) as batch:
                batch.drop_column("tenant_id")
