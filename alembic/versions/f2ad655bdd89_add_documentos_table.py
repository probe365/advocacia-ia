"""add documentos table

Revision ID: f2ad655bdd89
Revises: 0009_merge_heads_fix
Create Date: 2025-11-23 17:29:35.952313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2ad655bdd89'
down_revision: Union[str, None] = '0009_merge_heads_fix'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
