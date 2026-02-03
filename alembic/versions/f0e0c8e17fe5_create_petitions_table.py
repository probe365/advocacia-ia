"""create petitions table

Revision ID: f0e0c8e17fe5
Revises: e4a4e6dd66ae
Create Date: 2025-12-28 19:33:07.809596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f0e0c8e17fe5'
down_revision: Union[str, None] = 'e4a4e6dd66ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("petitions"):
        return

    op.create_table(
        "petitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Text(), nullable=True),
        sa.Column("process_id", sa.Text(), nullable=True),
        sa.Column("petition_type", sa.String(length=100), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_petitions_tenant", "petitions", ["tenant_id"], unique=False)
    op.create_index("ix_petitions_process", "petitions", ["process_id"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("petitions"):
        op.drop_index("ix_petitions_process", table_name="petitions")
        op.drop_index("ix_petitions_tenant", table_name="petitions")
        op.drop_table("petitions")
    op.add_column('clientes', sa.Column('email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('data_cadastro', sa.DATE(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('observacoes', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('cpf_cnpj', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('telefone', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('nome_completo', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('clientes', sa.Column('tipo_pessoa', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('clientes', sa.Column('responsavel_pj', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('profissao', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('rg_ie', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('estado_civil', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('clientes', sa.Column('endereco_completo', sa.TEXT(), autoincrement=False, nullable=True))
    op.create_unique_constraint('clientes_cpf_cnpj_key', 'clientes', ['cpf_cnpj'], postgresql_nulls_not_distinct=False)
    op.drop_column('clientes', 'nome')
    op.create_table('partes_adversas',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id_processo', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tipo_parte', sa.VARCHAR(length=20), autoincrement=False, nullable=False, comment='Valores: autor, reu, terceiro_interessado, litisconsorte'),
    sa.Column('nome_completo', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('cpf_cnpj', sa.VARCHAR(length=18), autoincrement=False, nullable=True),
    sa.Column('rg', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('qualificacao', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('endereco_completo', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('bairro', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('cidade', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('estado', sa.VARCHAR(length=2), autoincrement=False, nullable=True),
    sa.Column('cep', sa.VARCHAR(length=9), autoincrement=False, nullable=True),
    sa.Column('telefone', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('advogado_nome', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('advogado_oab', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('observacoes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['id_processo'], ['processos.id_processo'], name='fk_partes_adversas_processo', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='partes_adversas_pkey'),
    comment='Cadastro de partes adversas vinculadas a processos'
    )
    op.create_index('idx_partes_adversas_tipo', 'partes_adversas', ['tipo_parte'], unique=False)
    op.create_index('idx_partes_adversas_tenant_processo', 'partes_adversas', ['tenant_id', 'id_processo'], unique=False)
    op.create_index('idx_partes_adversas_tenant', 'partes_adversas', ['tenant_id'], unique=False)
    op.create_index('idx_partes_adversas_processo', 'partes_adversas', ['id_processo'], unique=False)
    op.create_index('idx_partes_adversas_nome', 'partes_adversas', ['nome_completo'], unique=False)
    op.create_index('idx_partes_adversas_cpf_cnpj', 'partes_adversas', ['cpf_cnpj'], unique=False)
    op.create_table('advogados',
    sa.Column('oab', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('nome', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('email', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('area_atuacao', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(length=255), server_default=sa.text("'public'::character varying"), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('oab', name='advogados_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('chat_turns',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id_processo', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('role', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['id_processo'], ['processos.id_processo'], name='fk_chat_turns_processo', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='chat_turns_pkey')
    )
    op.create_index('ix_chat_turns_tenant', 'chat_turns', ['tenant_id'], unique=False)
    op.create_index('ix_chat_turns_processo', 'chat_turns', ['id_processo'], unique=False)
    # ### end Alembic commands ###
