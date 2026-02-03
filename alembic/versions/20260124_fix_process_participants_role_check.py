"""expand process_participants role check

Revision ID: 20260124_fix_pp_role
Revises: 20260124_multitenant_fixes
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260124_fix_pp_role"
down_revision: Union[str, None] = "20260124_multitenant_fixes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("process_participants"):
        existing_checks = {check["name"] for check in inspector.get_check_constraints("process_participants")}
        if "ck_pp_role" in existing_checks:
            op.drop_constraint("ck_pp_role", "process_participants", type_="check")

        op.create_check_constraint(
            "ck_pp_role",
            "process_participants",
            "role IN ('autor','reu','terceiro','assistente','outro','reclamante','reclamada')",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("process_participants"):
        existing_checks = {check["name"] for check in inspector.get_check_constraints("process_participants")}
        if "ck_pp_role" in existing_checks:
            op.drop_constraint("ck_pp_role", "process_participants", type_="check")

        op.create_check_constraint(
            "ck_pp_role",
            "process_participants",
            "role IN ('autor','reu','terceiro','assistente','outro')",
        )
