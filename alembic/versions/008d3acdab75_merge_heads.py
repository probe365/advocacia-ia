"""merge heads

Revision ID: 008d3acdab75
Revises: 0004_add_tipo_parte_to_processos, 0007_add_trigger_cnj_immutable
Create Date: 2025-11-17 23:54:37.813680

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008d3acdab75'
down_revision = ('0004_add_tipo_parte_to_processos', '0007_add_trigger_cnj_immutable')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass