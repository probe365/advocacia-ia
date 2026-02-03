"""add admin user

Revision ID: add_admin_user_20251230
Revises: f0e0c8e17fe5
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_admin_user_20251230'
down_revision = 'f0e0c8e17fe5'
branch_labels = None
depends_on = None

def upgrade():
    # Substitua o hash abaixo pelo hash real da sua aplicação
    op.execute(
        sa.text(
            """
            INSERT INTO usuarios (username, email, password_hash, nome_completo, data_criacao, tenant_id)
            VALUES ('admin', 'admin@seudominio.com', 'admin365', 'Administrador', '2025-12-30T23:59:00', 'public')
            """
        )
    )

def downgrade():
    op.execute(
        sa.text(
            "DELETE FROM usuarios WHERE username = :username AND tenant_id = :tenant_id"
        ),
        {"username": "admin", "tenant_id": "public"}
    )