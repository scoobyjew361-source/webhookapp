"""add processed updates and reminder fields

Revision ID: 0003_processed_updates
Revises: 0002_add_plan_id_to_payments
Create Date: 2026-03-07 14:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_processed_updates"
down_revision: Union[str, Sequence[str], None] = "0002_add_plan_id_to_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "leads",
        sa.Column("reminder_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )

    op.create_table(
        "processed_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processed_updates_update_id", "processed_updates", ["update_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_processed_updates_update_id", table_name="processed_updates")
    op.drop_table("processed_updates")

    op.drop_column("leads", "reminder_count")
    op.drop_column("leads", "last_reminder_at")
