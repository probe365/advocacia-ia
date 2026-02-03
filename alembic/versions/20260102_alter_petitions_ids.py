"""alter petitions tenant and cliente ids to text

Revision ID: 20260102_alter_petitions_ids
Revises: add_admin_user_20251230
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260102_alter_petitions_ids"
down_revision: Union[str, None] = "add_admin_user_20251230"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_column(inspector, table: str, column: str):
    for col in inspector.get_columns(table):
        if col["name"] == column:
            return col
    return None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("petitions"):
        return

    tenant_col = _get_column(inspector, "petitions", "tenant_id")
    cliente_col = _get_column(inspector, "petitions", "cliente_id")

    with op.batch_alter_table("petitions", schema="public") as batch_op:
        if tenant_col and not isinstance(tenant_col["type"], sa.String):
            batch_op.alter_column(
                "tenant_id",
                existing_type=tenant_col["type"],
                type_=sa.Text(),
                existing_nullable=False,
                postgresql_using="tenant_id::text",
            )
        if cliente_col and not isinstance(cliente_col["type"], sa.String):
            batch_op.alter_column(
                "cliente_id",
                existing_type=cliente_col["type"],
                type_=sa.Text(),
                existing_nullable=True,
                postgresql_using="cliente_id::text",
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("petitions"):
        return

    tenant_col = _get_column(inspector, "petitions", "tenant_id")
    cliente_col = _get_column(inspector, "petitions", "cliente_id")

    with op.batch_alter_table("petitions", schema="public") as batch_op:
        if cliente_col and isinstance(cliente_col["type"], sa.Text):
            batch_op.alter_column(
                "cliente_id",
                existing_type=sa.Text(),
                type_=postgresql.UUID(),
                existing_nullable=True,
                postgresql_using="cliente_id::uuid",
            )
        if tenant_col and isinstance(tenant_col["type"], sa.Text):
            batch_op.alter_column(
                "tenant_id",
                existing_type=sa.Text(),
                type_=sa.Integer(),
                existing_nullable=False,
                postgresql_using="tenant_id::integer",
            )
