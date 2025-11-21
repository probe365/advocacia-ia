"""merge heads

Revision ID: 6f23dab2abf0
Revises: 0002_add_tenant_columns, 3ef67bdf723f
Create Date: 2025-11-18 19:59:57.884145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f23dab2abf0'
down_revision = ('0002_add_tenant_columns', '3ef67bdf723f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass