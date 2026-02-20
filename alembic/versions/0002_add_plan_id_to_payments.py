"""add plan_id to payments

Revision ID: 0002_add_plan_id_to_payments
Revises: 0001_init_tables
Create Date: 2026-02-19 19:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_plan_id_to_payments"
down_revision: Union[str, Sequence[str], None] = "0001_init_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("plan_id", sa.String(length=20), nullable=True))
    op.execute("UPDATE payments SET plan_id = 'basic' WHERE plan_id IS NULL")
    op.alter_column("payments", "plan_id", nullable=False)


def downgrade() -> None:
    op.drop_column("payments", "plan_id")
