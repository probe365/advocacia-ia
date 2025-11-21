"""Item 3 - Create partes_adversas table

Revision ID: 0006_create_partes_adversas
Revises: 0005_add_processos_fields
Create Date: 2025-11-12 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006_create_partes_adversas'
down_revision = '0005_add_processos_fields'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabela partes_adversas para Item 3 da reformatação.
    
    Permite cadastrar múltiplas partes adversas por processo:
    - Autor (parte contrária ao cliente)
    - Réu (quando cliente é autor)
    - Terceiro interessado
    - Litisconsortes
    
    Inclui dados completos de qualificação.
    """
    
    op.create_table(
        'partes_adversas',
        
        # Chave primária
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Relacionamentos
        sa.Column('id_processo', sa.Integer(), nullable=False,
                 comment='FK para processos - qual processo esta parte pertence'),
        sa.Column('tenant_id', sa.String(length=50), nullable=False,
                 comment='Isolamento multi-tenant'),
        
        # Tipo de parte
        sa.Column('tipo_parte', sa.String(length=20), nullable=False,
                 comment='autor, reu, terceiro_interessado, litisconsorte'),
        
        # Dados pessoais/empresariais
        sa.Column('nome_completo', sa.String(length=255), nullable=False,
                 comment='Nome completo da pessoa física ou razão social da PJ'),
        sa.Column('cpf_cnpj', sa.String(length=18), nullable=True,
                 comment='CPF (com máscara XXX.XXX.XXX-XX) ou CNPJ (XX.XXX.XXX/XXXX-XX)'),
        sa.Column('rg', sa.String(length=20), nullable=True,
                 comment='RG (apenas para pessoa física)'),
        sa.Column('qualificacao', sa.Text(), nullable=True,
                 comment='Profissão, estado civil, nacionalidade - texto livre'),
        
        # Endereço completo
        sa.Column('endereco_completo', sa.Text(), nullable=True,
                 comment='Logradouro, número, complemento'),
        sa.Column('bairro', sa.String(length=100), nullable=True),
        sa.Column('cidade', sa.String(length=100), nullable=True),
        sa.Column('estado', sa.String(length=2), nullable=True,
                 comment='UF - sigla com 2 letras'),
        sa.Column('cep', sa.String(length=9), nullable=True,
                 comment='CEP com máscara XXXXX-XXX'),
        
        # Contato
        sa.Column('telefone', sa.String(length=20), nullable=True,
                 comment='Telefone com DDD'),
        sa.Column('email', sa.String(length=255), nullable=True),
        
        # Advogado da parte adversa (se conhecido)
        sa.Column('advogado_nome', sa.String(length=255), nullable=True,
                 comment='Nome do advogado da parte adversa'),
        sa.Column('advogado_oab', sa.String(length=20), nullable=True,
                 comment='OAB do advogado adverso (ex: SP 123456)'),
        
        # Observações
        sa.Column('observacoes', sa.Text(), nullable=True,
                 comment='Notas adicionais sobre a parte'),
        
        # Auditoria
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), 
                 onupdate=sa.func.now(), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_processo'], ['processos.id_processo'], 
                       name='fk_partes_adversas_processo',
                       ondelete='CASCADE')  # Se processo deletado, deletar partes
    )
    
    # Índices para performance
    op.create_index('idx_partes_adversas_processo', 'partes_adversas', ['id_processo'])
    op.create_index('idx_partes_adversas_tenant', 'partes_adversas', ['tenant_id'])
    op.create_index('idx_partes_adversas_cpf_cnpj', 'partes_adversas', ['cpf_cnpj'])
    op.create_index('idx_partes_adversas_nome', 'partes_adversas', ['nome_completo'])
    op.create_index('idx_partes_adversas_tipo', 'partes_adversas', ['tipo_parte'])
    
    # Índice composto para queries multi-tenant + processo
    op.create_index('idx_partes_adversas_tenant_processo', 'partes_adversas', 
                   ['tenant_id', 'id_processo'])
    
    print("✅ Migration 0006 concluída: Tabela partes_adversas criada com sucesso")


def downgrade():
    """
    Remove tabela partes_adversas.
    """
    
    # Remover índices
    op.drop_index('idx_partes_adversas_tenant_processo', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_tipo', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_nome', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_cpf_cnpj', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_tenant', table_name='partes_adversas')
    op.drop_index('idx_partes_adversas_processo', table_name='partes_adversas')
    
    # Remover tabela
    op.drop_table('partes_adversas')
    
    print("⏪ Migration 0006 revertida: Tabela partes_adversas removida")
