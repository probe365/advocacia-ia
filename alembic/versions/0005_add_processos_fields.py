"""Item 1 - Add new fields to processos table

Revision ID: 0005_add_processos_fields
Revises:0004_add_tipo_parte_to_processo
Create Date: 2025-11-11 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005_add_processos_fields'
down_revision = '0004_add_tipo_parte_to_processos'
branch_labels = None
depends_on = None


def upgrade():
    # Todos os campos e índices já existem na tabela base. Nada a fazer nesta migração.
    pass
    
    
def downgrade():
    # Todos os campos e índices já existem na tabela base. Nada a fazer nesta migração.
    pass
    