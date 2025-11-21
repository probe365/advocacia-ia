"""Create chat_turns table

Revision ID: 0003_create_chat_turns
Revises: 0001_create_core_tables
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_create_chat_turns'
down_revision = '0001_create_core_tables'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'chat_turns',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('id_processo', sa.Integer, nullable=False),
        sa.Column('role', sa.String, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('tenant_id', sa.String, nullable=True),
    )
    op.create_foreign_key('fk_chat_turns_processo', 'chat_turns', 'processos', ['id_processo'], ['id_processo'], ondelete='CASCADE')
    op.create_index('ix_chat_turns_processo', 'chat_turns', ['id_processo'])
    op.create_index('ix_chat_turns_tenant', 'chat_turns', ['tenant_id'])

def downgrade():
    op.drop_index('ix_chat_turns_tenant', table_name='chat_turns')
    op.drop_index('ix_chat_turns_processo', table_name='chat_turns')
    op.drop_constraint('fk_chat_turns_processo', 'chat_turns', type_='foreignkey')
    op.drop_table('chat_turns')
