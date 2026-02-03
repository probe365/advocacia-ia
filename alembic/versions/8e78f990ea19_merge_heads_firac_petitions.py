"""merge heads firac + petitions

Revision ID: 8e78f990ea19
Revises: 05a4938b1d3f, fe27daee6505
Create Date: 2026-01-10 22:01:52.656739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e78f990ea19'
down_revision: Union[str, None] = ('05a4938b1d3f', 'fe27daee6505')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
