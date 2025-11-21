"""Baseline empty migration

Revision ID: 0001_baseline
Revises: 
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Tables already created manually by application startup. Future diffs will go here.
    pass

def downgrade():
    pass
