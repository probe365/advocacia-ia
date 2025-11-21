"""Add tenant_id columns

Revision ID: 0002_add_tenant_columns
Revises: 0001_create_core_tables
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_tenant_columns'
down_revision = '0001_create_core_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Adds tenant_id nullable first; later a backfill + not null + default can be enforced.
    with op.batch_alter_table('clientes', schema=None) as batch:
        batch.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch.create_index('ix_clientes_tenant_id', ['tenant_id'])
    with op.batch_alter_table('processos', schema=None) as batch:
        batch.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch.create_index('ix_processos_tenant_id', ['tenant_id'])
    with op.batch_alter_table('usuarios', schema=None) as batch:
        batch.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch.create_index('ix_usuarios_tenant_id', ['tenant_id'])


def downgrade():
    with op.batch_alter_table('usuarios', schema=None) as batch:
        batch.drop_index('ix_usuarios_tenant_id')
        batch.drop_column('tenant_id')
    with op.batch_alter_table('processos', schema=None) as batch:
        batch.drop_index('ix_processos_tenant_id')
        batch.drop_column('tenant_id')
    with op.batch_alter_table('clientes', schema=None) as batch:
        batch.drop_index('ix_clientes_tenant_id')
        batch.drop_column('tenant_id')
