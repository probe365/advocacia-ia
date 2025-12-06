"""Merge heads from divergent branches.

Revision ID: 0009_merge_heads_fix
Revises: 0004_add_tipo_parte_to_processos, 0007_add_trigger_cnj_immutable
Create Date: 2025-11-22 23:59:00.000000
"""

from alembic import op
import sqlalchemy as sa

# Identificadores
revision = '0009_merge_heads_fix'
down_revision = (
    '0002_create_usuarios_table',
    '6f23dab2abf0'
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
