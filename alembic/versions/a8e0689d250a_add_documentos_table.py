"""add documentos table

Revision ID: a8e0689d250a
Revises: f2ad655bdd89
Create Date: 2025-11-23 17:31:27.265567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8e0689d250a'
down_revision: Union[str, None] = 'f2ad655bdd89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Tabela documentos já existe no banco (criada manualmente)
    # Esta migration serve apenas para alinhar o Alembic.
    pass


def downgrade():
    # Não vamos remover a tabela existente na volta
    pass
