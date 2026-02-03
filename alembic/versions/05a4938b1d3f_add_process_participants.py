"""add process_participants

Revision ID: 05a4938b1d3f
Revises: rev_20260102_petition_tpl
Create Date: 2026-01-07 00:29:14.376954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05a4938b1d3f'
down_revision: Union[str, None] = 'rev_20260102_petition_tpl'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    table_name = "process_participants"
    inspector = sa.inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    table_already_exists = table_name in existing_tables

    if not table_already_exists:
        op.create_table(
            table_name,
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.Text(), nullable=False),
            sa.Column("process_id", sa.Text(), nullable=False),
            sa.Column("party_kind", sa.Text(), nullable=False),
            sa.Column("party_id", sa.Text(), nullable=False),
            sa.Column("role", sa.Text(), nullable=False),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    else:
        required_columns = {
            "id",
            "tenant_id",
            "process_id",
            "party_kind",
            "party_id",
            "role",
            "is_primary",
            "created_at",
            "updated_at",
        }
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = required_columns - existing_columns
        if missing_columns:
            raise RuntimeError(
                "Tabela process_participants existe, mas faltam colunas obrigatórias: "
                + ", ".join(sorted(missing_columns))
            )

    existing_checks = {check["name"] for check in inspector.get_check_constraints(table_name)} if table_already_exists else set()
    if "ck_pp_party_kind" not in existing_checks:
        op.create_check_constraint(
            "ck_pp_party_kind",
            table_name,
            "party_kind IN ('cliente','adverso')"
        )
    if "ck_pp_role" not in existing_checks:
        op.create_check_constraint(
            "ck_pp_role",
            table_name,
            "role IN ('autor','reu','terceiro','assistente','outro')"
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)} if table_already_exists else set()
    if "ix_pp_process" not in existing_indexes:
        op.create_index(
            "ix_pp_process",
            table_name,
            ["tenant_id", "process_id"],
            unique=False,
        )
    if "ix_pp_party" not in existing_indexes:
        op.create_index(
            "ix_pp_party",
            table_name,
            ["tenant_id", "party_kind", "party_id"],
            unique=False,
        )
    if "ux_pp_unique" not in existing_indexes:
        op.create_index(
            "ux_pp_unique",
            table_name,
            ["tenant_id", "process_id", "party_kind", "party_id", "role"],
            unique=True,
        )

    # 1 principal por role por processo
    op.execute("""
      CREATE UNIQUE INDEX IF NOT EXISTS ux_pp_primary_per_role
      ON process_participants(tenant_id, process_id, role)
      WHERE is_primary = TRUE;
      """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_pp_primary_per_role;")
    op.drop_index("ux_pp_unique", table_name="process_participants")
    op.drop_index("ix_pp_party", table_name="process_participants")
    op.drop_index("ix_pp_process", table_name="process_participants")
    op.drop_table("process_participants")
