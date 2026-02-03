"""add DJE email ingestion and andamento filters

Revision ID: 20260129_add_dje_email_and_filters
Revises: 20260128_add_dje_tables
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260129_add_dje_email_and_filters"
down_revision: Union[str, None] = "20260128_add_dje_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("dje_andamentos"):
        if "tipo_comunicacao" not in [c["name"] for c in inspector.get_columns("dje_andamentos")]:
            op.add_column("dje_andamentos", sa.Column("tipo_comunicacao", sa.String(length=64), nullable=True))

    if inspector.has_table("dje_email_messages"):
        op.rename_table("dje_email_messages", "dje_email_messages_legacy")

    op.create_table(
        "dje_email_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("process_number", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("movement_at", sa.DateTime(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("message_id", sa.String(length=255), nullable=True),
        sa.Column("dedupe_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dje_email_messages_tenant", "dje_email_messages", ["tenant_id"])
    op.create_index("ix_dje_email_messages_process_number", "dje_email_messages", ["process_number"])
    op.create_unique_constraint(
        "uq_dje_email_messages_dedupe",
        "dje_email_messages",
        ["tenant_id", "dedupe_hash"],
    )

    if not inspector.has_table("dje_inbox_state"):
        op.create_table(
            "dje_inbox_state",
            sa.Column("tenant_id", sa.String(length=64), primary_key=True),
            sa.Column("mailbox", sa.String(length=255), primary_key=True),
            sa.Column("last_uid", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        )


def downgrade() -> None:
    op.drop_constraint("uq_dje_email_messages_dedupe", "dje_email_messages", type_="unique")
    op.drop_index("ix_dje_email_messages_process_number", table_name="dje_email_messages")
    op.drop_index("ix_dje_email_messages_tenant", table_name="dje_email_messages")
    op.drop_table("dje_email_messages")

    if op.get_bind().dialect.has_table(op.get_bind(), "dje_inbox_state"):
        op.drop_table("dje_inbox_state")

    if op.get_bind().dialect.has_table(op.get_bind(), "dje_andamentos"):
        op.drop_column("dje_andamentos", "tipo_comunicacao")
