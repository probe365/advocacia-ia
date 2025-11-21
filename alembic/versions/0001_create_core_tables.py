"""Create advogados, clientes, usuarios, and processos tables

Revision ID: 0001_create_core_tables
Revises: 
Create Date: 2025-11-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_create_core_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # advogados table
    op.create_table(
        'advogados',
        sa.Column('oab', sa.String(length=50), primary_key=True),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('area_atuacao', sa.String(length=100), nullable=True),
    )

    # clientes table
    op.create_table(
        'clientes',
        sa.Column('id_cliente', sa.Integer, primary_key=True),
        sa.Column('tipo_pessoa', sa.String(length=20), nullable=True),
        sa.Column('nome_completo', sa.String(length=255), nullable=False),
        sa.Column('cpf_cnpj', sa.String(length=20), nullable=True),
        sa.Column('rg_ie', sa.String(length=20), nullable=True),
        sa.Column('nacionalidade', sa.String(length=50), nullable=True),
        sa.Column('estado_civil', sa.String(length=30), nullable=True),
        sa.Column('profissao', sa.String(length=100), nullable=True),
        sa.Column('endereco_completo', sa.String(length=255), nullable=True),
        sa.Column('telefone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('responsavel_pj', sa.String(length=255), nullable=True),
        sa.Column('data_cadastro', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('observacoes', sa.Text, nullable=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.UniqueConstraint('cpf_cnpj', name='clientes_cpf_cnpj_key'),
    )
    op.create_index('ix_clientes_tenant_id', 'clientes', ['tenant_id'])

    # usuarios table
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(length=150), nullable=False, unique=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nome_completo', sa.String(length=255), nullable=True),
        sa.Column('data_criacao', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('advogado_oab', sa.String(length=50), nullable=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['advogado_oab'], ['advogados.oab'], name='usuarios_advogado_oab_fkey'),
    )
    op.create_index('ix_usuarios_tenant_id', 'usuarios', ['tenant_id'])

    # processos table
    op.create_table(
        'processos',
        sa.Column('id_processo', sa.Integer, primary_key=True),
        sa.Column('id_cliente', sa.Integer, nullable=False),
        sa.Column('nome_caso', sa.String(length=255), nullable=True),
        sa.Column('numero_cnj', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('data_inicio', sa.Date, nullable=True),
        sa.Column('advogado_oab', sa.String(length=50), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('tipo_parte', sa.String(length=50), nullable=True),
        sa.Column('local_tramite', sa.Text, nullable=True),
        sa.Column('comarca', sa.String(length=100), nullable=True),
        sa.Column('area_atuacao', sa.String(length=50), nullable=True),
        sa.Column('instancia', sa.String(length=20), nullable=True),
        sa.Column('subfase', sa.String(length=50), nullable=True),
        sa.Column('assunto', sa.String(length=255), nullable=True),
        sa.Column('valor_causa', sa.Numeric(15, 2), nullable=True),
        sa.Column('data_distribuicao', sa.Date, nullable=True),
        sa.Column('data_encerramento', sa.Date, nullable=True),
        sa.Column('sentenca', sa.Text, nullable=True),
        sa.Column('em_execucao', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column('segredo_justica', sa.Boolean, nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['id_cliente'], ['clientes.id_cliente'], name='processos_id_cliente_fkey'),
        sa.ForeignKeyConstraint(['advogado_oab'], ['advogados.oab'], name='processos_advogado_oab_fkey'),
    )
    op.create_index('idx_processos_area_atuacao', 'processos', ['area_atuacao'])
    op.create_index('idx_processos_comarca', 'processos', ['comarca'])
    op.create_index('idx_processos_instancia', 'processos', ['instancia'])
    op.create_index('idx_processos_tenant_id', 'processos', ['tenant_id'])
    op.create_index('idx_processos_tipo_parte', 'processos', ['tipo_parte'])

def downgrade():
    op.drop_index('idx_processos_tipo_parte', table_name='processos')
    op.drop_index('idx_processos_tenant_id', table_name='processos')
    op.drop_index('idx_processos_instancia', table_name='processos')
    op.drop_index('idx_processos_comarca', table_name='processos')
    op.drop_index('idx_processos_area_atuacao', table_name='processos')
    op.drop_table('processos')
    op.drop_index('ix_usuarios_tenant_id', table_name='usuarios')
    op.drop_table('usuarios')
    op.drop_index('ix_clientes_tenant_id', table_name='clientes')
    op.drop_table('clientes')
    op.drop_table('advogados')