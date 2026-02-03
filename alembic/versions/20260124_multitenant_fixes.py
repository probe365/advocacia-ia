"""multi-tenant fixes for escritorio/usuarios/clientes

Revision ID: 20260124_multitenant_fixes
Revises: 8e78f990ea19
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260124_multitenant_fixes"
down_revision: Union[str, None] = "8e78f990ea19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _drop_unique_constraint_if_exists(inspector, table: str, columns: Sequence[str]) -> None:
    for constraint in inspector.get_unique_constraints(table):
        if set(constraint.get("column_names") or []) == set(columns):
            op.drop_constraint(constraint["name"], table, type_="unique")
            return


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- escritorio: ensure tenant_id ---
    if inspector.has_table("escritorio") and not _has_column(inspector, "escritorio", "tenant_id"):
        with op.batch_alter_table("escritorio") as batch:
            batch.add_column(sa.Column("tenant_id", sa.String(length=50), nullable=True))
            batch.create_index("ix_escritorio_tenant_id", ["tenant_id"])
        op.execute("UPDATE escritorio SET tenant_id = COALESCE(tenant_id, 'public')")
        with op.batch_alter_table("escritorio") as batch:
            batch.alter_column("tenant_id", nullable=False)
            batch.create_unique_constraint("uq_escritorio_tenant", ["tenant_id"])

    # --- usuarios: make username/email unique per tenant ---
    if inspector.has_table("usuarios"):
        _drop_unique_constraint_if_exists(inspector, "usuarios", ["username"])
        _drop_unique_constraint_if_exists(inspector, "usuarios", ["email"])
        with op.batch_alter_table("usuarios") as batch:
            batch.create_unique_constraint("uq_usuarios_tenant_username", ["tenant_id", "username"])
            batch.create_unique_constraint("uq_usuarios_tenant_email", ["tenant_id", "email"])

    # --- advogados: add tenant_id and unique per tenant ---
    if inspector.has_table("advogados") and not _has_column(inspector, "advogados", "tenant_id"):
        with op.batch_alter_table("advogados") as batch:
            batch.add_column(sa.Column("tenant_id", sa.String(length=50), nullable=True))
            batch.create_index("ix_advogados_tenant_id", ["tenant_id"])
        op.execute("UPDATE advogados SET tenant_id = COALESCE(tenant_id, 'public')")
        with op.batch_alter_table("advogados") as batch:
            batch.alter_column("tenant_id", nullable=False)
            batch.create_unique_constraint("uq_advogados_tenant_oab", ["tenant_id", "oab"])

    # --- clientes: make cpf_cnpj unique per tenant ---
    if inspector.has_table("clientes"):
        _drop_unique_constraint_if_exists(inspector, "clientes", ["cpf_cnpj"])
        with op.batch_alter_table("clientes") as batch:
            batch.create_unique_constraint("uq_clientes_tenant_cpf_cnpj", ["tenant_id", "cpf_cnpj"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("clientes"):
        _drop_unique_constraint_if_exists(inspector, "clientes", ["tenant_id", "cpf_cnpj"])
        with op.batch_alter_table("clientes") as batch:
            batch.create_unique_constraint("clientes_cpf_cnpj_key", ["cpf_cnpj"])

    if inspector.has_table("usuarios"):
        _drop_unique_constraint_if_exists(inspector, "usuarios", ["tenant_id", "username"])
        _drop_unique_constraint_if_exists(inspector, "usuarios", ["tenant_id", "email"])
        with op.batch_alter_table("usuarios") as batch:
            batch.create_unique_constraint("usuarios_username_key", ["username"])
            batch.create_unique_constraint("usuarios_email_key", ["email"])

    if inspector.has_table("advogados") and _has_column(inspector, "advogados", "tenant_id"):
        with op.batch_alter_table("advogados") as batch:
            batch.drop_constraint("uq_advogados_tenant_oab", type_="unique")
            batch.drop_index("ix_advogados_tenant_id")
            batch.drop_column("tenant_id")

    if inspector.has_table("escritorio") and _has_column(inspector, "escritorio", "tenant_id"):
        with op.batch_alter_table("escritorio") as batch:
            batch.drop_constraint("uq_escritorio_tenant", type_="unique")
            batch.drop_index("ix_escritorio_tenant_id")
            batch.drop_column("tenant_id")
