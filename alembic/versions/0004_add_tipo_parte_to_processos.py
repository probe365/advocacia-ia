"""Add tipo_parte column to processos table

This migration adds the 'tipo_parte' column to track whether the client is:
- 'autor' (plaintiff/claimant)
- 'reu' (defendant)
- 'terceiro' (third party)
- 'reclamante' (complainant in labor cases)
- 'reclamada' (respondent in labor cases)

Revision ID: 0004_add_tipo_parte_to_processos
Revises: 0003_create_chat_turns
Create Date: 2025-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_add_tipo_parte_to_processos'
down_revision = '0003_create_chat_turns'
branch_labels = None
depends_on = None

def upgrade():
    # tipo_parte column already exists in base table; nothing to do here
    pass

def downgrade():
    # tipo_parte column already exists in base table; nothing to do here
    pass
