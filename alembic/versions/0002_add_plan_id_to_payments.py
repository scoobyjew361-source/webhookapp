"""keep revision chain

Revision ID: 0002_add_plan_id_to_payments
Revises: 0001_init_tables
Create Date: 2026-02-19 19:30:00
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0002_add_plan_id_to_payments"
down_revision: Union[str, Sequence[str], None] = "0001_init_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intentionally empty. The previous domain-specific migration was removed.
    pass


def downgrade() -> None:
    pass
