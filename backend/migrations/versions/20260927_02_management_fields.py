"""Add farmer, procurement, and payment management fields safely."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_02"
down_revision = "20260927_01"
branch_labels = None
depends_on = None


def _columns(bind, table):
    return {column["name"] for column in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    farmer_columns = _columns(bind, "farmers")
    if "is_active" not in farmer_columns:
        op.add_column("farmers", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    procurement_columns = _columns(bind, "procurement")
    for name, column in {
        "rejected_quantity": sa.Column("rejected_quantity", sa.Float(), nullable=False, server_default="0"),
        "remarks": sa.Column("remarks", sa.Text(), nullable=True),
        "procurement_date": sa.Column("procurement_date", sa.DateTime(), nullable=True),
    }.items():
        if name not in procurement_columns:
            op.add_column("procurement", column)

    payment_columns = _columns(bind, "payments")
    for name, column in {
        "payment_method": sa.Column("payment_method", sa.String(30), nullable=True),
        "failure_reason": sa.Column("failure_reason", sa.Text(), nullable=True),
        "created_at": sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    }.items():
        if name not in payment_columns:
            op.add_column("payments", column)


def downgrade() -> None:
    pass
