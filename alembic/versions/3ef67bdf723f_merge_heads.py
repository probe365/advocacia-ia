"""merge heads

Revision ID: 3ef67bdf723f
Revises: 0001_create_core_tables, 008d3acdab75, 4df8693b13dc
Create Date: 2025-11-18 17:36:16.631652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ef67bdf723f'
down_revision = ('0001_create_core_tables', '008d3acdab75', '4df8693b13dc')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass