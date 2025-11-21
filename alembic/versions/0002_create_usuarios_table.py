"""Create usuarios table

Revision ID: 0002_create_usuarios_table
Revises: 0001_create_core_tables
Create Date: 2025-11-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_create_usuarios_table'
down_revision = '0001_create_core_tables'
branch_labels = None
depends_on = None

def upgrade():
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
    )

def downgrade():
    op.drop_table('usuarios')