"""add process_firac table

Revision ID: fe27daee6505
Revises: 6f23dab2abf0
Create Date: <auto>
"""

from alembic import op
import sqlalchemy as sa


# 🔁 Ajuste esses 2 campos com os valores que o Alembic gerou
revision = "fe27daee6505"
down_revision = "6f23dab2abf0"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ✅ Idempotência: se você já criou a tabela no pgAdmin4, não quebra
    exists = conn.execute(sa.text("SELECT to_regclass('public.process_firac')")).scalar()
    if exists:
        # Mesmo não criando nada, a revisão será marcada no alembic_version.
        return

    op.create_table(
        "process_firac",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("process_id", sa.String(length=128), nullable=False),

        sa.Column("facts", sa.Text, nullable=True),
        sa.Column("issue", sa.Text, nullable=True),
        sa.Column("rules", sa.Text, nullable=True),
        sa.Column("application", sa.Text, nullable=True),
        sa.Column("conclusion", sa.Text, nullable=True),

        sa.Column("created_by_user_id", sa.BigInteger, nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'ui'")),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ✅ Evita duplicidade: 1 FIRAC por tenant+processo+source (ex: ui, api, system)
    op.create_unique_constraint(
        "uq_process_firac_tenant_process_source",
        "process_firac",
        ["tenant_id", "process_id", "source"],
    )

    # ✅ Índices úteis para listagem e busca
    op.create_index("ix_process_firac_tenant", "process_firac", ["tenant_id"])
    op.create_index("ix_process_firac_process", "process_firac", ["process_id"])
    op.create_index("ix_process_firac_tenant_process", "process_firac", ["tenant_id", "process_id"])

    # ✅ Trigger para updated_at (PostgreSQL)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS trigger AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ language plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_process_firac_updated_at
        BEFORE UPDATE ON public.process_firac
        FOR EACH ROW
        EXECUTE PROCEDURE public.set_updated_at();
        """
    )


def downgrade():
    conn = op.get_bind()

    exists = conn.execute(sa.text("SELECT to_regclass('public.process_firac')")).scalar()
    if not exists:
        return

    # remove trigger
    op.execute("DROP TRIGGER IF EXISTS trg_process_firac_updated_at ON public.process_firac;")

    # OBS: não removo a function set_updated_at() porque pode ser reutilizada por outras tabelas.
    # Se você quiser remover MESMO, só faça se tiver certeza de que nada mais usa:
    # op.execute("DROP FUNCTION IF EXISTS public.set_updated_at();")

    op.drop_index("ix_process_firac_tenant_process", table_name="process_firac")
    op.drop_index("ix_process_firac_process", table_name="process_firac")
    op.drop_index("ix_process_firac_tenant", table_name="process_firac")
    op.drop_constraint("uq_process_firac_tenant_process_source", "process_firac", type_="unique")
    op.drop_table("process_firac")
