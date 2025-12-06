"""Item 3 - Create partes_adversas table

Revision ID: 0006_create_partes_adversas
Revises: 0005_add_processos_fields
Create Date: 2025-11-12 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_create_partes_adversas'
down_revision = '0005_add_processos_fields'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabela partes_adversas com proteção contra duplicação.

    Se a tabela já existir (como no seu caso atual), apenas registra
    a migration como aplicada e segue em frente.
    """

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 👉 SE A TABELA JÁ EXISTE, NÃO TENTA CRIAR DE NOVO
    if inspector.has_table("partes_adversas"):
        op.get_context().impl.static_output(
            "⚠️ Tabela 'partes_adversas' já existe — ignorando criação na 0006."
        )
        return

    # 👉 SE NÃO EXISTE, CRIA NORMALMENTE
    op.create_table(
        'partes_adversas',

        # Chave primária
        sa.Column('id', sa.Integer(), nullable=False),

        # Relacionamentos
        sa.Column('id_processo', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),

        # Tipo de parte
        sa.Column('tipo_parte', sa.String(length=20), nullable=False),

        # Dados pessoais/empresariais
        sa.Column('nome_completo', sa.String(length=255), nullable=False),
        sa.Column('cpf_cnpj', sa.String(length=18), nullable=True),
        sa.Column('rg', sa.String(length=20), nullable=True),
        sa.Column('qualificacao', sa.Text(), nullable=True),

        # Endereço completo
        sa.Column('endereco_completo', sa.Text(), nullable=True),
        sa.Column('bairro', sa.String(length=100), nullable=True),
        sa.Column('cidade', sa.String(length=100), nullable=True),
        sa.Column('estado', sa.String(length=2), nullable=True),
        sa.Column('cep', sa.String(length=9), nullable=True),

        # Contato
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),

        # Advogado da parte adversa (se conhecido)
        sa.Column('advogado_nome', sa.String(length=255), nullable=True),
        sa.Column('advogado_oab', sa.String(length=20), nullable=True),

        # Observações
        sa.Column('observacoes', sa.Text(), nullable=True),

        # Auditoria
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                 onupdate=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['id_processo'],
            ['processos.id_processo'],
            name='fk_partes_adversas_processo',
            ondelete='CASCADE'
        ),
    )

    # Índices
    op.create_index('idx_partes_adversas_processo', 'partes_adversas', ['id_processo'])
    op.create_index('idx_partes_adversas_tenant', 'partes_adversas', ['tenant_id'])
    op.create_index('idx_partes_adversas_cpf_cnpj', 'partes_adversas', ['cpf_cnpj'])
    op.create_index('idx_partes_adversas_nome', 'partes_adversas', ['nome_completo'])
    op.create_index('idx_partes_adversas_tipo', 'partes_adversas', ['tipo_parte'])
    op.create_index(
        'idx_partes_adversas_tenant_processo',
        'partes_adversas',
        ['tenant_id', 'id_processo']
    )

    print("✅ Migration 0006 executada: Tabela partes_adversas criada.")


def downgrade():
    """
    Remove tabela partes_adversas.
    """

    op.drop_index('idx_partes_adversas_tenant_processo', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_tipo', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_nome', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_cpf_cnpj', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_tenant', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_processo', table_name='partes_adversas')

    op.drop_table('partes_adversas')

    print("⏪ Migration 0006 revertida: Tabela partes_adversas removida")
