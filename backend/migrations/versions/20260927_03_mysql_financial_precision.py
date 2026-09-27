"""Use fixed-precision values for procurement and payment calculations."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_03"
down_revision = "20260927_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("procurement") as batch:
        batch.alter_column("actual_weight", existing_type=sa.Float(), type_=sa.Numeric(12, 3), existing_nullable=True)
        batch.alter_column("rejected_quantity", existing_type=sa.Float(), type_=sa.Numeric(12, 3), existing_nullable=False)
        batch.alter_column("rate", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=True)
        batch.alter_column("total_amount", existing_type=sa.Float(), type_=sa.Numeric(14, 2), existing_nullable=True)
    with op.batch_alter_table("payments") as batch:
        batch.alter_column("amount", existing_type=sa.Float(), type_=sa.Numeric(14, 2), existing_nullable=True)


def downgrade() -> None:
    # Financial precision is intentionally not downgraded automatically.
    pass
