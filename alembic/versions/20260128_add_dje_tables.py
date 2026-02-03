"""add DJE push and andamento tables

Revision ID: 20260128_add_dje_tables
Revises: 20260124_fix_pp_role, 20260124_convert_ids_to_text
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260128_add_dje_tables"
down_revision: Union[str, None] = ("20260124_fix_pp_role", "20260124_convert_ids_to_text")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dje_push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("process_id", sa.String(length=64), nullable=False),
        sa.Column("cnj_number", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dje_push_subscriptions_tenant", "dje_push_subscriptions", ["tenant_id"])
    op.create_index("ix_dje_push_subscriptions_process", "dje_push_subscriptions", ["process_id"])
    op.create_unique_constraint(
        "uq_dje_push_subscriptions_tenant_process",
        "dje_push_subscriptions",
        ["tenant_id", "process_id"],
    )

    op.create_table(
        "dje_push_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("process_id", sa.String(length=64), nullable=False),
        sa.Column("cnj_number", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=True),
        sa.Column("event_title", sa.String(length=255), nullable=True),
        sa.Column("event_date", sa.DateTime(), nullable=True),
        sa.Column("prazo_final", sa.DateTime(), nullable=True),
        sa.Column("status_ciencia", sa.String(length=64), nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("origem", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dje_push_events_tenant", "dje_push_events", ["tenant_id"])
    op.create_index("ix_dje_push_events_process", "dje_push_events", ["process_id"])
    op.create_index("ix_dje_push_events_event_date", "dje_push_events", ["event_date"])
    op.create_unique_constraint(
        "uq_dje_push_events_tenant_process_hash",
        "dje_push_events",
        ["tenant_id", "process_id", "event_hash"],
    )

    op.create_table(
        "dje_andamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("process_id", sa.String(length=64), nullable=False),
        sa.Column("cnj_number", sa.String(length=64), nullable=False),
        sa.Column("movimento_data", sa.DateTime(), nullable=True),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("tribunal", sa.String(length=64), nullable=True),
        sa.Column("orgao", sa.String(length=128), nullable=True),
        sa.Column("grau", sa.String(length=64), nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("origem", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dje_andamentos_tenant", "dje_andamentos", ["tenant_id"])
    op.create_index("ix_dje_andamentos_process", "dje_andamentos", ["process_id"])
    op.create_index("ix_dje_andamentos_data", "dje_andamentos", ["movimento_data"])
    op.create_unique_constraint(
        "uq_dje_andamentos_tenant_process_hash",
        "dje_andamentos",
        ["tenant_id", "process_id", "event_hash"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_dje_andamentos_tenant_process_hash", "dje_andamentos", type_="unique")
    op.drop_index("ix_dje_andamentos_data", table_name="dje_andamentos")
    op.drop_index("ix_dje_andamentos_process", table_name="dje_andamentos")
    op.drop_index("ix_dje_andamentos_tenant", table_name="dje_andamentos")
    op.drop_table("dje_andamentos")

    op.drop_constraint("uq_dje_push_events_tenant_process_hash", "dje_push_events", type_="unique")
    op.drop_index("ix_dje_push_events_event_date", table_name="dje_push_events")
    op.drop_index("ix_dje_push_events_process", table_name="dje_push_events")
    op.drop_index("ix_dje_push_events_tenant", table_name="dje_push_events")
    op.drop_table("dje_push_events")

    op.drop_constraint("uq_dje_push_subscriptions_tenant_process", "dje_push_subscriptions", type_="unique")
    op.drop_index("ix_dje_push_subscriptions_process", table_name="dje_push_subscriptions")
    op.drop_index("ix_dje_push_subscriptions_tenant", table_name="dje_push_subscriptions")
    op.drop_table("dje_push_subscriptions")
